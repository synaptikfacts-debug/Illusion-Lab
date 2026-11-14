"""Neutron-star collision renderer (moderngl). Units: total mass M = 1, G = c = 1."""
import argparse, math, os, subprocess, sys
import cv2, moderngl, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TAU = 2 * math.pi


def sm(a, b, v):
    x = np.clip((v - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def cam_from(d, el, az, fov, roll, tgt=(0, 0, 0)):
    el, az, roll = math.radians(el), math.radians(az), math.radians(roll)
    tgt = np.array(tgt, float)
    pos = tgt + np.array([d * math.cos(el) * math.cos(az), d * math.sin(el), d * math.cos(el) * math.sin(az)])
    fwd = tgt - pos; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0.0, 1.0, 0.0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    cr, sr = math.cos(roll), math.sin(roll)
    right, up = cr * right + sr * up, -sr * right + cr * up
    return pos, right, up, fwd, math.tan(math.radians(fov) / 2)


def make_post(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = (xx - W / 2) / H, (yy - H / 2) / H
    vig = (1 - 0.32 * (dx * dx + dy * dy) * 2.2).astype(np.float32)[..., None]

    def post(img):
        lum = (img @ np.float32([0.2126, 0.7152, 0.0722]))[..., None]
        img = np.maximum(lum + (img - lum) * 1.25, 0)
        br = np.maximum(img - 0.75, 0)
        q = cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bl = 0.40 * cv2.GaussianBlur(q, (0, 0), 2.0) + 0.25 * cv2.GaussianBlur(q, (0, 0), 9) + 0.10 * cv2.GaussianBlur(q, (0, 0), 34)
        img = img + cv2.resize(bl, (W, H), interpolation=cv2.INTER_LINEAR)
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        x = img * 0.9
        img = np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)
        img = img ** (1 / 2.2) * vig
        return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    return post


class Renderer:
    def __init__(self, W, H, ss):
        self.W, self.H, self.ss = W, H, ss
        self.ctx = moderngl.create_standalone_context(require=330, **({'backend': 'egl'} if os.environ.get('BH_EGL') else {}))
        vs = "#version 330\nin vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }"
        self.prog = self.ctx.program(vertex_shader=vs, fragment_shader=open(os.path.join(HERE, 'ns.frag')).read())
        self.vao = self.ctx.simple_vertex_array(self.prog, self.ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], 'f4')), 'p')
        N = 128
        rng = np.random.default_rng(5)
        k = np.fft.fftfreq(N) * N
        kk = np.sqrt(k[:, None, None] ** 2 + k[None, :, None] ** 2 + k[None, None, :] ** 2)
        spec = np.fft.fftn(rng.standard_normal((N, N, N))) / np.maximum(kk, 1.0) ** 1.55
        spec[0, 0, 0] = 0
        vol = np.real(np.fft.ifftn(spec)); vol = np.clip((vol - vol.mean()) / (vol.std() * 4) + 0.5, 0, 1).astype('f4')
        self.noise = self.ctx.texture3d((N, N, N), 1, vol.tobytes(), dtype='f4')
        self.noise.repeat_x = self.noise.repeat_y = self.noise.repeat_z = True
        self.noise.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.noise.use(0)
        self.RW, self.RH = W * ss, H * ss
        self.tex = self.ctx.texture((self.RW, self.RH), 4, dtype='f4')
        self.fbo = self.ctx.framebuffer([self.tex])
        self.level = int(round(math.log2(ss)))

    def frame(self, u, cam):
        pos, right, up, fwd, tanf = cam
        u = dict(u, res=(float(self.RW), float(self.RH)), camPos=tuple(pos), camR=tuple(right), camU=tuple(up), camF=tuple(fwd), tanF=tanf, noiseTex=0)
        for k, v in u.items():
            if k in self.prog:
                self.prog[k].value = v
        self.fbo.use()
        self.vao.render(moderngl.TRIANGLE_STRIP)
        self.tex.build_mipmaps(0, self.level)
        img = np.frombuffer(self.tex.read(level=self.level), np.float32).reshape(self.H, self.W, 4)[::-1, :, :3]
        return np.nan_to_num(img, nan=0.0, posinf=50.0, neginf=0.0)


def still_state(sep=7.6, phase=0.35, t=3.0):
    p1 = (0.5 * sep * math.cos(phase), 0.0, 0.5 * sep * math.sin(phase))
    p2 = (-p1[0], 0.0, -p1[2])
    return dict(T=t, p1=p1, p2=p2, rad=0.9, stretch=1.3, mass=0.14, bridge=1.0, gwAmp=0.035, gwK=18.0, gwW=6.0, gwPhase=0.0, glow=1.0, orbPhase=phase, armAmp=1.0)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--w', type=int, default=1080); ap.add_argument('--h', type=int, default=1920); ap.add_argument('--ss', type=int, default=2)
    a = ap.parse_args()
    R = Renderer(a.w, a.h, a.ss)
    post = make_post(a.w, a.h)
    img = post(R.frame(still_state(), cam_from(40.0, 38.0, -70.0, 40.0, -8.0)))
    cv2.imwrite(a.out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print('saved', a.out)
