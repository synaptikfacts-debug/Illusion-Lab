#version 330
// Binary neutron star inspiral: two lensing compact stars, tidal stretching, a glowing matter bridge,
// gravitational waves rippling through a colourful nebula behind them.
uniform vec2 res;
uniform vec3 camPos, camR, camU, camF;
uniform float tanF, T;
uniform vec3 p1, p2;          // star centres
uniform float rad;            // star radius
uniform float stretch;        // tidal elongation along the separation axis (1 = sphere)
uniform float mass;           // lensing strength of each star
uniform float bridge;         // brightness of the matter bridge / tails
uniform float gwAmp, gwK, gwW, gwPhase;   // gravitational-wave ripple
uniform float glow;           // magnetosphere glow
uniform float orbPhase, armAmp;   // spiral arms of stripped gas
uniform sampler3D noiseTex;
out vec4 frag;

const float PI = 3.14159265, TAU = 6.2831853;
float nz(vec3 p) { return texture(noiseTex, p).r; }
float wrapPi(float a) { return a - TAU * floor((a + PI) / TAU); }
vec3 hash33(vec3 p) { p = fract(p * vec3(0.1031, 0.1030, 0.0973)); p += dot(p, p.yxz + 33.33); return fract((p.xxy + p.yxx) * p.zyx); }

vec3 sky(vec3 d) {
    // gravitational waves: a quadrupole ripple that shears the background as it passes
    vec3 ax = normalize(cross(p2 - p1, vec3(0.0, 0.0, 1.0)) + vec3(0.0, 1.0, 0.0) * 1e-3);
    float th = acos(clamp(dot(d, -normalize(camPos)), -1.0, 1.0));
    float ph = atan(dot(d, camU), dot(d, camR));
    float wave = sin(th * gwK - gwW * T + 2.0 * ph + gwPhase) * gwAmp * smoothstep(0.02, 0.15, th);
    vec3 q = normalize(d + wave * (camR * cos(ph) + camU * sin(ph)));
    vec3 col = vec3(0.002, 0.003, 0.008);
    // nebula: violet / teal / rose clouds
    float n1 = nz(q * 0.45 + 0.13), n2 = nz(q * 0.9 + 0.61), n3 = nz(q * 2.1 + 0.37);
    float cloud = smoothstep(0.42, 0.82, n1 * 0.55 + n2 * 0.45) * (0.5 + 0.9 * n3);
    vec3 nc = mix(vec3(0.42, 0.22, 1.0), vec3(0.1, 0.75, 0.9), smoothstep(0.35, 0.7, n2));
    nc = mix(nc, vec3(1.0, 0.3, 0.6), smoothstep(0.6, 0.85, n3) * 0.6);
    col += cloud * nc * 0.09;
    for (int l = 0; l < 2; l++) {
        float K = (l == 0) ? 35.0 : 100.0;
        vec3 c = q * K, ci = floor(c), h = hash33(ci + float(l) * 91.0);
        if (h.x < ((l == 0) ? 0.14 : 0.07)) {
            vec3 dd = c - (ci + 0.25 + 0.5 * h); dd -= q * dot(dd, q);
            float b = pow(h.y, 6.0) * ((l == 0) ? 8.0 : 1.4) + 0.05;
            col += mix(vec3(0.7, 0.8, 1.0), vec3(1.0, 0.85, 0.7), h.z) * b * 2.0 * exp(-dot(dd, dd) / ((l == 0) ? 0.004 : 0.008));
        }
    }
    return col;
}

// signed distance-ish test to a tidally stretched star
float starD(vec3 x, vec3 c, vec3 ax) {
    vec3 d = x - c;
    float a = dot(d, ax);
    vec3 perp = d - a * ax;
    vec3 s = perp + ax * (a / stretch);
    return length(s) - rad;
}

vec3 starColor(vec3 x, vec3 c, vec3 ax, vec3 v, float id) {
    vec3 n = normalize(x - c);
    float mu = abs(dot(n, normalize(v)));
    float spin = T * 2.5 + id * 2.0;
    vec3 m = vec3(n.x * cos(spin) - n.z * sin(spin), n.y, n.x * sin(spin) + n.z * cos(spin));
    float cells = nz(m * 2.2 + id * 0.37);
    float fine = nz(m * 7.0 + 0.5);
    float spots = smoothstep(0.62, 0.8, nz(m * 0.9 + 0.2 + id));     // magnetic hot spots
    vec3 base = mix(vec3(0.45, 0.65, 1.0), vec3(0.92, 0.96, 1.0), smoothstep(0.3, 0.8, cells * 0.6 + fine * 0.4));
    float I = (0.55 + 0.45 * pow(mu, 0.5)) * (1.1 + 0.35 * cells + 0.15 * fine) + 1.2 * spots;
    I += 1.2 * pow(1.0 - mu, 3.0);                                   // bright rim
    I *= 1.0 + 1.5 * (stretch - 1.0) * max(dot(n, ax * (id < 0.5 ? 1.0 : -1.0)), 0.0);
    return base * I * 1.0;
}

void main() {
    vec2 uv = (gl_FragCoord.xy / res) * 2.0 - 1.0;
    uv.x *= res.x / res.y;
    vec3 dir = normalize(camF + (uv.x * camR + uv.y * camU) * tanF);
    vec3 x = camPos, v = dir;
    float jit = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
    vec3 ax = normalize(p2 - p1);
    vec3 acc = vec3(0.0);
    bool hit = false;
    for (int i = 0; i < 2400; i++) {
        vec3 d1 = x - p1, d2 = x - p2;
        float r1 = length(d1), r2 = length(d2);
        float dmin = min(r1, r2) - rad * stretch;
        float dt = clamp(0.35 * dmin, 0.02, 3.0);
        if (abs(x.y) < 4.0 && length(x.xz) < 27.0) dt = min(dt, 0.06) * (0.6 + 0.8 * fract(jit + float(i) * 0.6180339));
        // weak-field light bending toward both stars (deflection 4M/b)
        vec3 a = -2.0 * mass * (d1 / (r1 * r1 * r1) + d2 / (r2 * r2 * r2));
        a -= dot(a, v) * v;
        // magnetosphere glow + matter bridge (emission along the ray)
        float g1 = exp(-max(r1 - rad, 0.0) / (rad * 0.6)), g2 = exp(-max(r2 - rad, 0.0) / (rad * 0.6));
        acc += vec3(0.4, 0.6, 1.0) * glow * (g1 * g1 + g2 * g2) * 0.05 * dt;
        if (bridge > 0.0) {
            vec3 m = 0.5 * (p1 + p2);
            float along = dot(x - m, ax);
            float L = 0.5 * length(p2 - p1);
            vec3 perp = (x - m) - along * ax;
            float w = rad * (0.35 + 0.5 * (1.0 - abs(along) / (L + 1e-3)));
            float tube = exp(-dot(perp, perp) / (w * w)) * smoothstep(L + rad, L * 0.2, abs(along));
            float fil = 0.6 + 0.8 * nz(vec3(along * 0.15 + T * 0.4, length(perp) * 0.6, 0.3));
            acc += mix(vec3(0.5, 0.75, 1.0), vec3(1.0, 0.85, 0.95), fil * 0.5) * bridge * tube * fil * 0.12 * dt;
        }
        if (armAmp > 0.0 && abs(x.y) < 4.0) {
            float r = length(x.xz);
            if (r > 1.2 && r < 26.0) {
                float phi = atan(x.z, x.x);
                float arm = 0.0;
                for (int k = 0; k < 2; k++) {
                    float dp = wrapPi(phi - orbPhase - 1.7 * log(r / 2.5) - float(k) * PI);
                    float w = 0.45 + 0.12 * r;
                    float q = dp * r / w;
                    arm += exp(-q * q * 0.5);
                }
                float pr = phi - orbPhase;
                vec3 cw = vec3(cos(pr) * r * 0.22, sin(pr) * r * 0.22, x.y * 0.8);
                float fil = nz(cw * 0.37 + vec3(0.11, 0.23, 0.31)) * 0.65 + nz(cw * 1.13 + vec3(0.57, 0.19, 0.71)) * 0.35;
                float dens = arm * pow(clamp(fil * 1.6 - 0.25, 0.0, 2.0), 2.2);
                float prof = smoothstep(1.2, 3.5, r) * (1.0 - smoothstep(9.0, 24.0, r)) * exp(-x.y * x.y / (0.03 + 0.006 * r * r));
                vec3 ac = mix(vec3(0.6, 0.8, 1.0), vec3(0.62, 0.35, 1.0), smoothstep(3.0, 9.0, r));
                ac = mix(ac, vec3(1.0, 0.32, 0.62), smoothstep(9.0, 18.0, r));
                acc += ac * armAmp * dens * prof * 1.6 * dt;
            }
        }
        if (starD(x, p1, ax) < 0.0) { acc += starColor(x, p1, ax, v, 0.0); hit = true; break; }
        if (starD(x, p2, ax) < 0.0) { acc += starColor(x, p2, ax, v, 1.0); hit = true; break; }
        v = normalize(v + a * dt);
        x += v * dt;
        if (length(x) > 400.0) break;
    }
    if (!hit) acc += sky(v);
    frag = vec4(acc, 1.0);
}
