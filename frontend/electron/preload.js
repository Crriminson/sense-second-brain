const { contextBridge } = require('electron');

// Expose any APIs to the renderer process here if needed
contextBridge.exposeInMainWorld('electron', {
  platform: process.platform,
});
