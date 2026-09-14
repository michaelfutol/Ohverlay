// Execute the actual overlay script with a small deterministic Canvas/DOM host.
// Run with: node --test tests/test_cosmos_branching.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const CYCLE_MS = 8 * 60 * 60 * 1000;
const STORE_KEY = 'ohverlay.cosmos.v1';
const EPOCH = Date.UTC(2026, 8, 13, 4);
const html = fs.readFileSync(path.join(__dirname, '../marketplace-overlays/cosmos-overlay.html'), 'utf8');
const script = Array.from(html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi), match => match[1]).join('\n');

function host(query) {
  let now = EPOCH;
  let nextFrame = 0;
  let drawCalls = 0;
  const drawImages = [];
  const frames = new Map();
  const events = new Map();
  const storage = new Map([[STORE_KEY, JSON.stringify({ start: EPOCH - 2 * CYCLE_MS })]]);
  const gradient = { addColorStop() {} };
  const canvasContext = {};
  for (const method of [
    'setTransform', 'clearRect', 'beginPath', 'closePath', 'moveTo', 'lineTo',
    'quadraticCurveTo', 'bezierCurveTo', 'stroke', 'fill', 'save', 'restore',
    'translate', 'rotate', 'scale', 'ellipse', 'arc', 'rect', 'fillRect', 'clip',
  ]) {
    canvasContext[method] = (...args) => {
      drawCalls++;
      for (const arg of args) if (typeof arg === 'number') assert.ok(Number.isFinite(arg), `${method} received ${arg}`);
    };
  }
  canvasContext.createLinearGradient = canvasContext.createRadialGradient = () => gradient;
  canvasContext.drawImage = (...args) => { drawCalls++; drawImages.push(args); };
  function element() {
    const listeners = new Map();
    return {
      value: '', textContent: '', hidden: true, style: {}, dataset: {},
      addEventListener(name, fn) { listeners.set(name, fn); },
      emit(name) { assert.ok(listeners.has(name), `missing ${name} listener`); listeners.get(name)({ target: this }); },
      getContext() { return canvasContext; },
      setAttribute() {},
    };
  }
  const elements = new Map(['world', 'controls', 'size', 'sizeValue', 'flowerSize', 'flowerSizeValue', 'species'].map(id => [id, element()]));
  class Clock extends Date {
    constructor(...args) { super(...(args.length ? args : [now])); }
    static now() { return now; }
  }
  class SpriteImage {
    constructor() { this.complete = true; this.naturalWidth = 1254; this.naturalHeight = 1254; this.src = ''; }
  }
  const context = {
    Date: Clock, Math, URLSearchParams, console, Image: SpriteImage,
    innerWidth: 1440, innerHeight: 900, devicePixelRatio: 1.5,
    location: { search: query },
    performance: { now: () => now - EPOCH },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, String(value)),
    },
    addEventListener(name, fn) { events.set(name, fn); },
    requestAnimationFrame(fn) { frames.set(++nextFrame, fn); return nextFrame; },
    cancelAnimationFrame(id) { frames.delete(id); },
    document: { hidden: false, getElementById: id => elements.get(id), addEventListener() {} },
  };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(script, context, { filename: 'cosmos-overlay.html', timeout: 2000 });
  assert.equal(typeof context._cosmos.snapshot, 'function', 'overlay exposes its live branch geometry');
  return {
    context, elements, storage,
    snapshot: () => context._cosmos.snapshot(),
    step(milliseconds = 16) {
      now += milliseconds;
      const callbacks = [...frames.values()];
      frames.clear();
      assert.ok(callbacks.length, 'overlay has a scheduled frame');
      callbacks.forEach(fn => fn(now - EPOCH));
    },
    resize(width, height) {
      context.innerWidth = width;
      context.innerHeight = height;
      assert.ok(events.has('resize'));
      events.get('resize')();
    },
    get drawCalls() { return drawCalls; }, drawImages,
  };
}

function cubic(points, t) {
  const u = 1 - t;
  return {
    x: u ** 3 * points[0].x + 3 * u * u * t * points[1].x + 3 * u * t * t * points[2].x + t ** 3 * points[3].x,
    y: u ** 3 * points[0].y + 3 * u * u * t * points[1].y + 3 * u * t * t * points[2].y + t ** 3 * points[3].y,
  };
}

function near(a, b, message) {
  assert.ok(Math.hypot(a.x - b.x, a.y - b.y) < 1e-6, message);
}

function assertConnected(scene, count) {
  assert.equal(scene.rootCount, 1, 'every flower shares a single plant root');
  assert.equal(scene.segments.length, count);
  assert.equal(scene.heads.length, count);
  const segments = new Map(scene.segments.map(segment => [segment.id, segment]));
  assert.equal(segments.size, count, 'segment identifiers are unique');
  assert.equal(new Set(scene.heads.map(head => head.id)).size, count, 'head identifiers are unique');
  const roots = scene.segments.filter(segment => segment.parentId === null);
  assert.equal(roots.length, 1);
  assert.equal(roots[0].kind, 'trunk');
  for (const segment of scene.segments) {
    assert.ok(['trunk', 'shoot', 'fork'].includes(segment.kind));
    assert.equal(segment.points.length, 4, 'each stem is represented by a cubic curve');
    for (const point of segment.points) {
      assert.ok(Number.isFinite(point.x) && Number.isFinite(point.y), 'stem points are finite');
    }
    if (segment.parentId === null) continue;
    assert.notEqual(segment.kind, 'trunk', 'only the shared root is a trunk');
    const parent = segments.get(segment.parentId);
    assert.ok(parent, `${segment.id} has an existing parent`);
    assert.ok(segment.attachT > 0 && segment.attachT < 1, 'branches emerge from stem nodes');
    near(segment.points[0], cubic(parent.points, segment.attachT), `${segment.id} remains joined to its parent`);
    const ancestors = new Set([segment.id]);
    let cursor = segment;
    while (cursor.parentId !== null) {
      assert.ok(!ancestors.has(cursor.parentId), 'the branching graph contains no cycles');
      ancestors.add(cursor.parentId);
      cursor = segments.get(cursor.parentId);
      assert.ok(cursor, 'all ancestors exist');
    }
    assert.equal(cursor.id, roots[0].id, 'every branch connects to the same root');
  }
  for (const head of scene.heads) {
    const segment = segments.get(head.segmentId);
    assert.ok(segment, `${head.id} belongs to an existing branch`);
    near(head, segment.points[3], `${head.id} stays at its branch tip`);
    assert.ok(head.stage !== undefined, 'heads retain lifecycle state');
  }
}

for (const species of ['bipinnatus', 'sulphureus']) {
  for (const count of [1, 2, 3, 7, 9, 12]) {
    test(`${species}: ${count} flower sites form one connected plant through an eight-hour cycle`, () => {
      const app = host(`?count=${count}&species=${species}&controls=1`);
      const initial = app.snapshot();
      assertConnected(initial, count);
      const ids = Array.from(initial.segments, segment => segment.id);
      const startingAge = app.context._cosmos.lifecycle(0).age;
      for (let phase = 1; phase <= 16; phase++) {
        app.step(CYCLE_MS / 16);
        const scene = app.snapshot();
        assertConnected(scene, count);
        assert.deepEqual(Array.from(scene.segments, segment => segment.id), ids, 'bloom replacement preserves the parent plant');
        if (phase === 8) assert.ok(Math.abs(app.context._cosmos.lifecycle(0).age - startingAge) > .4, 'the lifecycle actually advances');
      }
      assert.ok(Math.abs(app.context._cosmos.lifecycle(0).age - startingAge) < 1e-9, 'one cycle lasts eight hours');
      assert.ok(app.drawCalls > 0, 'the renderer executed as well as the geometry model');
    });
  }
}

test('root sway carries every flower while branches stay attached', () => {
  const app = host('?count=9&species=bipinnatus');
  app.context._cosmos.physics[0].bend = 0;
  const before = app.snapshot();
  app.context._cosmos.physics[0].bend = .14;
  const after = app.snapshot();
  assertConnected(after, 9);
  for (const head of after.heads) {
    const previous = before.heads.find(value => value.id === head.id);
    assert.ok(Math.hypot(head.x - previous.x, head.y - previous.y) > .1, `${head.id} inherits root sway`);
  }
  app.step();
  assertConnected(app.snapshot(), 9);
});

test('cursor contact on a side shoot gently carries force into the shared stem', () => {
  const app = host('?count=9&species=bipinnatus');
  const before = app.snapshot();
  const shoot = before.segments.find(segment => segment.kind === 'shoot');
  const tip = shoot.points[3];
  const cursor = { x: tip.x - 20, y: tip.y };
  const trunk = before.segments.find(segment => segment.kind === 'trunk');
  // Keep the cursor clear of the trunk so its response must travel from a shoot.
  for (const t of [.25, .5, .75, 1]) {
    const point = cubic(trunk.points, t);
    assert.ok(Math.hypot(point.x - cursor.x, point.y - cursor.y) > 100 * trunk.unit);
  }
  app.context.__onCursorMove(cursor.x, cursor.y);
  for (let frame = 0; frame < 60; frame++) app.step();
  assert.ok(Math.abs(app.context._cosmos.physics[shoot.index].bend) > .001, 'the touched shoot responds');
  assert.ok(Math.abs(app.context._cosmos.physics[0].bend) > .0001, 'the shared root inherits part of the force');
  assertConnected(app.snapshot(), 9);
  app.context.__onCursorLeave();
});

test('initial growth keeps flowers and new branches attached from the first frame', () => {
  const app = host('?count=9&species=bipinnatus');
  app.context._cosmos.state.start = EPOCH;
  assertConnected(app.snapshot(), 9);
  for (let hour = 1; hour <= 8; hour++) {
    app.step(CYCLE_MS / 8);
    assertConnected(app.snapshot(), 9);
  }
});

test('resize and live size/species controls keep the plant connected without restarting blooms', () => {
  const app = host('?count=7&species=bipinnatus&controls=1');
  const before = app.snapshot();
  const saved = app.storage.get(STORE_KEY);
  const age = app.context._cosmos.lifecycle(0).age;
  app.resize(800, 600);
  const resized = app.snapshot();
  assertConnected(resized, 7);
  assert.ok(resized.heads.some((head, i) => Math.hypot(head.x - before.heads[i].x, head.y - before.heads[i].y) > 1), 'resizing repositions the plant');
  app.resize(1440, 900);
  app.elements.get('size').value = '150';
  app.elements.get('size').emit('input');
  assert.equal(app.context._cosmos.state.scale, 1.5);
  const scaled = app.snapshot();
  assertConnected(scaled, 7);
  assert.ok(scaled.heads.some((head, i) => Math.hypot(head.x - resized.heads[i].x, head.y - resized.heads[i].y) > 1), 'the size control changes rendered geometry');
  app.elements.get('flowerSize').value = '240';
  app.elements.get('flowerSize').emit('input');
  assert.equal(app.context._cosmos.state.flowerSizePx, 240, 'the flower slider changes bloom diameter independently');
  assert.equal(app.elements.get('flowerSizeValue').textContent, '2.5 in');
  assert.equal(app.snapshot().flowerSizePx, 240);
  app.elements.get('species').value = 'sulphureus';
  app.elements.get('species').emit('change');
  assert.equal(app.context._cosmos.state.species, 'sulphureus');
  assertConnected(app.snapshot(), 7);
  assert.equal(app.storage.get(STORE_KEY), saved, 'live controls preserve the stored lifecycle origin');
  assert.equal(app.context._cosmos.lifecycle(0).age, age, 'live controls preserve bloom progress');
  app.step();
});

test('flower diameter defaults to two inches and remains independently adjustable', () => {
  const app = host('?flowersize=240&controls=1');
  assert.equal(app.context._cosmos.state.flowerSizePx, 240);
  assert.equal(app.elements.get('flowerSize').value, '240');
  assert.equal(app.elements.get('flowerSizeValue').textContent, '2.5 in');
  app.context.setFlowerSize(400);
  assert.equal(app.context._cosmos.state.flowerSizePx, 288, 'the size API clamps to the control range');
  const defaultApp = host('?controls=1');
  assert.equal(defaultApp.context._cosmos.state.flowerSizePx, 192);
  assert.equal(defaultApp.elements.get('flowerSizeValue').textContent, '2.0 in');
});

test('Sulphur Cosmos uses its transparent orange bloom sprite while it opens', () => {
  const app = host('?species=sulphureus&controls=1');
  assert.equal(app.context._cosmos.state.flowerSizePx, 192);
  app.context._cosmos.state.start = EPOCH - CYCLE_MS * .23;
  app.step();
  assert.ok(app.drawImages.length > 0, 'mature sulphur blooms use the realistic flower asset');
  assert.ok(app.drawImages.every(args => args[0].src === 'assets/cosmos-sulphureus-flower.png'));
  assert.ok(app.drawImages[0][3] > 0 && app.drawImages[0][3] < 192, 'the flower sprite grows into its selected diameter');
});

test('whole flower heads stay in view across window sizes, scale settings, and stem sway', () => {
  const outside = [];
  for (const species of ['bipinnatus', 'sulphureus']) {
    for (const count of [3, 9, 12]) {
      const app = host(`?count=${count}&species=${species}`);
      for (const [width, height] of [[640, 480], [1280, 800]]) {
        app.resize(width, height);
        for (const scale of [.5, 1, 1.5, 2.2]) {
          app.context.setScale(scale);
          for (const bend of [-.15, 0, .15]) {
            for (const physics of app.context._cosmos.physics) physics.bend = bend;
            const scene = app.snapshot();
            assertConnected(scene, count);
            for (const head of scene.heads) {
              // Reserve a complete mature flower, including its ruffled tip,
              // even when this particular head is presently a small bud.
              const radius = scene.bloomRadius;
              if (head.x < radius || head.x > width - radius || head.y < radius || head.y > height - radius) {
                outside.push(`${species} count=${count} ${width}x${height} scale=${scale} bend=${bend}: ${head.id} at (${head.x.toFixed(1)}, ${head.y.toFixed(1)})`);
              }
            }
          }
        }
      }
    }
  }
  assert.equal(outside.length, 0, `${outside.length} heads fell outside the viewport:\n${outside.slice(0, 24).join('\n')}`);
});
