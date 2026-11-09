precision highp float;
varying vec3 vCol;
varying float vA;

void main() {
  vec2 c = gl_PointCoord - 0.5;
  float a = exp(-dot(c, c) * 18.0);
  if (a < 0.02) discard;
  gl_FragColor = vec4(vCol, a * vA);
}
