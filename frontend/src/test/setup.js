import '@testing-library/jest-dom';

// jsdom doesn't implement scrollIntoView
Element.prototype.scrollIntoView = () => {};

// react-activity-calendar checks CSS.supports when validating theme colors.
if (!globalThis.CSS) {
  globalThis.CSS = {};
}

if (!globalThis.CSS.supports) {
  globalThis.CSS.supports = () => true;
}

if (!window.matchMedia) {
  window.matchMedia = () => ({
    matches: false,
    media: '',
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

if (window.SVGElement && !window.SVGElement.prototype.getBBox) {
  window.SVGElement.prototype.getBBox = () => ({
    x: 0,
    y: 0,
    width: 0,
    height: 0,
  });
}
