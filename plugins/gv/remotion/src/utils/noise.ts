/** Simplified 2D Perlin noise for smooth orb movement. */
export function noise2D(x: number, y: number, seed: number = 0): number {
  const dot = (gx: number, gy: number, dx: number, dy: number) => gx * dx + gy * dy;

  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;

  const fade = (t: number) => t * t * t * (t * (t * 6 - 15) + 10);
  const u = fade(fx);
  const v = fade(fy);

  const hash = (xi: number, yi: number) => {
    let h = ((xi * 374761393 + yi * 668265263 + seed) ^ 0x5f3759df) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return h >>> 0;
  };

  const grad = (h: number, dx: number, dy: number) => {
    const angle = (h / 4294967296) * Math.PI * 2;
    return dot(Math.cos(angle), Math.sin(angle), dx, dy);
  };

  const n00 = grad(hash(ix, iy), fx, fy);
  const n10 = grad(hash(ix + 1, iy), fx - 1, fy);
  const n01 = grad(hash(ix, iy + 1), fx, fy - 1);
  const n11 = grad(hash(ix + 1, iy + 1), fx - 1, fy - 1);

  const nx0 = n00 + u * (n10 - n00);
  const nx1 = n01 + u * (n11 - n01);
  return nx0 + v * (nx1 - nx0);
}
