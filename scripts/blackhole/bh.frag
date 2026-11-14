#version 330
// Schwarzschild black hole (rs = 1): per-pixel geodesics through a VOLUMETRIC accretion disk
// with black-body colour, relativistic Doppler colour shift and beaming.
uniform vec2 res;
uniform vec3 camPos, camR, camU, camF;
uniform float tanF;
uniform float T;
uniform float flowA, flowB, flowW;
uniform float spinK;
uniform float T0;          // disk temperature scale (kelvin)
uniform float diskGain, beamK, expo;
uniform vec4 rip[6];
uniform vec4 spot[16];
uniform vec4 strA[3];
uniform vec4 strB[3];
uniform vec3 strN[3], strU[3], strC[3];   // stream orbit plane normal, in-plane axis, colour
uniform float shat, shatPh;
uniform float glit;
uniform vec4 star1; uniform vec3 star1c;
uniform vec4 neb;   uniform vec3 nebc;
uniform float nebSize;
uniform float skyRot;
uniform float bgNeb;       // colourful background nebulae (lensed)
uniform sampler3D noiseTex;
uniform float endK;        // ending: the hole swallows the disk (0..1)
uniform vec4 planet;       // centre xyz, radius (w <= 0: none)
uniform float wave;        // vertical ripple height scale
out vec4 frag;

const float PI = 3.14159265;
const float TAU = 6.2831853;

float sq(float x) { return x * x; }
vec3 hash33(vec3 p) { p = fract(p * vec3(0.1031, 0.1030, 0.0973)); p += dot(p, p.yxz + 33.33); return fract((p.xxy + p.yxx) * p.zyx); }
float wrapPi(float a) { return a - TAU * floor((a + PI) / TAU); }
float nz(vec3 p) { return texture(noiseTex, p).r; }

// black-body colour (normalised, linear), T in kelvin
vec3 bb(float t) {
    t = clamp(t, 1000.0, 40000.0) / 100.0;
    vec3 c;
    c.r = t <= 66.0 ? 1.0 : clamp(1.2929 * pow(t - 60.0, -0.1332), 0.0, 1.0);
    c.g = t <= 66.0 ? clamp(0.3901 * log(t) - 0.6318, 0.0, 1.0) : clamp(1.1298 * pow(t - 60.0, -0.0755), 0.0, 1.0);
    c.b = t >= 66.0 ? 1.0 : (t <= 19.0 ? 0.0 : clamp(0.5432 * log(t - 10.0) - 1.1963, 0.0, 1.0));
    return pow(c, vec3(2.2));
}

float scaleH(float r) { return 0.015 + 0.010 * r; }

// gas density of the disk at point p, sheared by the orbital flow
float density(vec3 p, float r) {
    float phi = atan(p.z, p.x);
    float H = scaleH(r);
    float om = sqrt(0.5 / (r * r * r)) * spinK;
    float lr = r * 0.22;
    float lift = 0.0;
    for (int i = 0; i < 6; i++) {
        if (rip[i].y > 0.0) lift += rip[i].y * wave * exp(-sq((r - rip[i].x) / (rip[i].z * 1.4)));
    }
    float yy = (p.y - lift * H * 2.2) / H;
    float pa = (phi - om * flowA) / TAU, pb = (phi - om * flowB) / TAU;
    float a1 = nz(vec3(pa * 3.0, lr, yy * 0.12)), b1 = nz(vec3(pb * 3.0, lr, yy * 0.12));
    float a2 = nz(vec3(pa * 8.0 + 0.37, lr * 3.1, yy * 0.25 + 0.5)), b2 = nz(vec3(pb * 8.0 + 0.37, lr * 3.1, yy * 0.25 + 0.5));
    float big = mix(b1, a1, flowW), fine = mix(b2, a2, flowW);
    float d = clamp(0.9 + 0.45 * (big - 0.5) + 0.4 * (fine - 0.5), 0.0, 2.0);
    d = d * d;
    float edge = 7.2 + 1.2 * (big - 0.5);
    float prof = smoothstep(2.3, 3.0, r) * (1.0 - smoothstep(edge - 2.6, edge, r));
    float rEnd = mix(30.0, 1.6, endK);
    prof *= 1.0 - smoothstep(rEnd - 2.5, rEnd, r);
    prof *= 1.0 + 3.0 * endK * exp(-sq((r - rEnd + 1.2) / 0.9));
    float vert = exp(-yy * yy * (1.0 + 0.6 * (fine - 0.5)));
    float rings = pow(max(0.5 + 0.5 * cos(TAU * (r - shatPh) / 1.25), 0.0), 3.0);
    d *= mix(1.0, 0.1 + 1.7 * rings, shat);
    return d * prof * vert;
}

// effects living in the mid-plane (ripples, clumps, streams, embers): emission only
vec3 planeFx(vec3 p, float g, float tobs) {
    float r = length(p.xz);
    if (r < 2.2 || r > 22.0) return vec3(0.0);
    float phi = atan(p.z, p.x);
    vec3 hot = bb(max(tobs, 3500.0) * 1.3);
    float e = 0.0;
    for (int i = 0; i < 6; i++) {
        if (rip[i].y > 0.0) e += rip[i].y * exp(-sq((r - rip[i].x) / rip[i].z));
    }
    e *= smoothstep(2.4, 3.2, r) * (1.0 - smoothstep(7.0, 9.5, r));
    for (int i = 0; i < 16; i++) {
        if (spot[i].z > 0.0) { vec2 d = p.xz - spot[i].xy; e += spot[i].z * exp(-dot(d, d) / (spot[i].w * spot[i].w)); }
    }
    vec3 col = hot * e;
    if (glit > 0.0) {
        float om = sqrt(0.5 / (r * r * r)) * spinK;
        float ph = phi - om * T;
        float ri = floor(r * 4.0);
        float na = 48.0 + ri * 6.0;
        float ai = floor(ph / TAU * na);
        vec3 h = hash33(vec3(ri, ai, 3.0));
        if (h.x > 0.9 && r < 10.0) {
            float rc = (ri + 0.2 + 0.6 * h.y) / 4.0, ac = (ai + 0.2 + 0.6 * h.z) / na * TAU;
            vec2 d2 = vec2(r - rc, rc * wrapPi(ph - ac));
            float tw = 0.5 + 0.5 * sin(T * (4.0 + 6.0 * h.y) + h.z * 40.0);
            col += bb(9000.0) * glit * 7.0 * tw * tw * exp(-dot(d2, d2) / 0.0012) * smoothstep(2.6, 3.4, r);
        }
    }
    return col * pow(max(g, 0.0), 3.0 * beamK);
}

vec3 streamFx(int k, vec3 p) {
    vec3 n = strN[k], u = strU[k], w2 = cross(n, u);
    float px = dot(p, u), py = dot(p, w2);
    float r = length(vec2(px, py));
    float psi0 = strA[k].x, rs = strA[k].y, c = strA[k].z;
    if (r > rs + 1.2 || r < 2.3) return vec3(0.0);
    float phi = atan(py, px);
    float e = 0.0;
    float psr = psi0 + c * log(rs / r);
    if (psr <= strB[k].x && psr >= strB[k].y) {
        float w = strA[k].w * (0.35 + 0.65 * r / rs);
        float along = clamp((psr - strB[k].y) / max(strB[k].x - strB[k].y, 1e-3), 0.0, 1.0);
        float lumpy = 0.6 + 0.8 * nz(vec3(psr * 0.9, r * 0.3, float(k) * 0.3));
        float d = r * wrapPi(phi - psr) / w;
        e += strB[k].z * (exp(-d * d) + 0.25 * exp(-d * d * 0.08)) * (0.3 + 0.7 * along * along) * lumpy;
    }
    float hr = rs * exp(-(strB[k].x - psi0) / c);
    vec2 dh = vec2(px, py) - hr * vec2(cos(strB[k].x), sin(strB[k].x));
    float hd = dot(dh, dh);
    e += strB[k].w * (exp(-hd / 0.2) + 0.04 * exp(-hd / 1.2));
    return strC[k] * e;
}

vec3 sky(vec3 d) {
    float cs = cos(skyRot), sn = sin(skyRot);
    vec3 q = vec3(cs * d.x - sn * d.z, d.y, sn * d.x + cs * d.z);
    vec3 col = vec3(0.0025, 0.0035, 0.008);
    float n1 = nz(q * 0.35 + 0.1), n2 = nz(q * 0.7 + 0.6), n3 = nz(q * 1.6 + 0.3);
    float cloud = smoothstep(0.45, 0.85, n1 * 0.6 + n2 * 0.4) * (0.6 + 0.8 * n3);
    vec3 nc = mix(vec3(1.0, 0.22, 0.45), vec3(0.15, 0.65, 0.8), smoothstep(0.35, 0.65, n2));
    nc = mix(nc, vec3(0.45, 0.25, 1.0), smoothstep(0.55, 0.8, n3) * 0.7);
    col += bgNeb * cloud * nc * 0.05;
    for (int l = 0; l < 2; l++) {
        float K = (l == 0) ? 30.0 : 90.0;
        vec3 c = q * K;
        vec3 ci = floor(c);
        vec3 h = hash33(ci + float(l) * 91.0);
        if (h.x < ((l == 0) ? 0.12 : 0.06)) {
            vec3 dd = c - (ci + 0.25 + 0.5 * h);
            dd -= q * dot(dd, q);
            float b = pow(h.y, 6.0) * ((l == 0) ? 7.0 : 1.2) + 0.04;
            col += mix(vec3(0.7, 0.8, 1.0), vec3(1.0, 0.8, 0.6), h.z) * b * 2.0 * exp(-dot(dd, dd) / ((l == 0) ? 0.0035 : 0.008));
        }
    }
    if (star1.w > 0.0) {
        float a = acos(clamp(dot(d, star1.xyz), -1.0, 1.0));
        col += star1c * star1.w * exp(-sq(a / 0.003)) * 25.0;
    }
    if (neb.w > 0.0) {
        float a = acos(clamp(dot(d, neb.xyz), -1.0, 1.0));
        col += nebc * neb.w * exp(-sq(a / nebSize)) * (0.3 + 1.4 * smoothstep(0.35, 0.75, nz(d * 0.8 + 0.2)));
    }
    return col;
}

void main() {
    vec2 uv = (gl_FragCoord.xy / res) * 2.0 - 1.0;
    uv.x *= res.x / res.y;
    vec3 dir = normalize(camF + (uv.x * camR + uv.y * camU) * tanF);
    vec3 x = camPos, v = dir;
    vec3 hv = cross(x, v);
    float h2 = dot(hv, hv);
    vec3 acc = vec3(0.0);
    float trans = 1.0;
    bool captured = false;
    for (int i = 0; i < 1100; i++) {
        float r = length(x);
        if (r < 1.0) { captured = true; break; }
        float dt = clamp(0.07 * (r - 0.85), 0.01, 0.9);
        float H = scaleH(r);
        bool near = r > 1.9 && r < 21.0;
        bool inSlab = near && abs(x.y) < 3.2 * H;
        if (inSlab) dt = min(dt, max(0.3 * H, 0.02));
        else if (near) dt = min(dt, max(abs(x.y) - 3.0 * H, 0.02) + 0.02);
        vec3 a = -1.5 * h2 * x / pow(r, 5.0);
        vec3 xn = x + v * dt + 0.5 * a * dt * dt;
        float rn = length(xn);
        vec3 an = -1.5 * h2 * xn / pow(rn, 5.0);
        vec3 vn = v + 0.5 * (a + an) * dt;
        if (planet.w > 0.0) {
            vec3 sg = xn - x;
            float tt = clamp(dot(planet.xyz - x, sg) / max(dot(sg, sg), 1e-6), 0.0, 1.0);
            vec3 dp = x + sg * tt - planet.xyz;
            if (dot(dp, dp) < planet.w * planet.w) {
                // shade the planet: lit by the disk below/inside, thin bright rim
                vec3 n = normalize(dp);
                vec3 L = normalize(-planet.xyz + vec3(0.0, 0.6 * sign(planet.y + 1e-3), 0.0));
                float lam = max(dot(n, L), 0.0);
                float rim = pow(1.0 - abs(dot(n, normalize(v))), 4.0);
                vec3 pc = vec3(1.0, 0.93, 0.85) * (0.9 * pow(lam, 3.0) + 0.25 * rim * lam) * (1.0 - endK) + vec3(0.004, 0.005, 0.008);
                acc += trans * pc;
                trans = 0.0;
                break;
            }
        }
        for (int k = 0; k < 3; k++) {
            if (strB[k].z <= 0.0 && strB[k].w <= 0.0) continue;
            float s0 = dot(x, strN[k]), s1 = dot(xn, strN[k]);
            if (s0 * s1 < 0.0) acc += trans * streamFx(k, mix(x, xn, s0 / (s0 - s1)));
        }
        bool cross0 = x.y * xn.y < 0.0;
        if (inSlab || (cross0 && near)) {
            vec3 u = normalize(v);
            vec3 pm = 0.5 * (x + xn);
            float rm = length(pm.xz);
            vec3 ephi = normalize(vec3(-pm.z, 0.0, pm.x));
            float beta = min(0.7, sqrt(0.5 / max(rm - 1.0, 0.35)));
            float D = sqrt(1.0 - beta * beta) / (1.0 - beta * dot(ephi, -u));
            float g = D * sqrt(max(1.0 - 1.0 / max(rm, 1.05), 0.05));
            float tprof = pow(3.0 / max(rm, 2.4), 0.75) * pow(max(1.0 - sqrt(2.4 / max(rm, 2.4)), 0.0) + 0.08, 0.25);
            float tobs = T0 * pow(3.0 / max(rm, 2.6), 1.5) * mix(1.0, g, 0.5);
            if (inSlab) {
                float rho = density(pm, max(rm, 1.9)) * diskGain;
                if (rho > 1e-4) {
                    float ds = dt * length(v);
                    float em = rho * pow(tprof, 3.0) * 55.0 * pow(max(g, 0.0), 3.0 * beamK + 1.0);
                    acc += trans * bb(tobs) * em * ds;
                    trans *= exp(-rho * 7.0 * ds);
                    if (trans < 0.004) break;
                }
            }
            if (cross0) {
                float f = x.y / (x.y - xn.y);
                acc += trans * planeFx(mix(x, xn, f), g, tobs) * 0.8;
            }
        }
        x = xn; v = vn;
        if (r > 70.0 && dot(x, v) > 0.0) break;
    }
    if (!captured && trans > 0.004 && trans > 0.0) acc += trans * sky(normalize(v));
    frag = vec4(acc * expo, 1.0);
}
