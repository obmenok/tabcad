window.dash_clientside = Object.assign({}, window.dash_clientside, {
  viewerFullscreen: {
    toggle: function(n) {
      if (!n) {
        return window.dash_clientside.no_update;
      }

      const panel = document.querySelector("#viewer-viewport-panel");
      if (!panel) {
        return "viewer-fullscreen:panel_not_found";
      }

      const pseudoClass = "viewer-pseudo-fullscreen";
      const activeClass = "viewer-pseudo-fullscreen-active";
      const nativeFullscreenElement = document.fullscreenElement || document.webkitFullscreenElement;
      const pseudoFullscreenElement = panel.classList.contains(pseudoClass);
      const requestFullscreen = panel.requestFullscreen || panel.webkitRequestFullscreen;
      const exitFullscreen = document.exitFullscreen || document.webkitExitFullscreen;

      function dispatchResize() {
        if (typeof Event === "function") {
          window.dispatchEvent(new Event("resize"));
          return;
        }

        const event = document.createEvent("Event");
        event.initEvent("resize", true, true);
        window.dispatchEvent(event);
      }

      function setPseudoFullscreen(active) {
        panel.classList.toggle(pseudoClass, active);
        document.documentElement.classList.toggle(activeClass, active);
        document.body.classList.toggle(activeClass, active);
        dispatchResize();
        setTimeout(dispatchResize, 120);
      }

      if (nativeFullscreenElement || pseudoFullscreenElement) {
        if (pseudoFullscreenElement) {
          setPseudoFullscreen(false);
          return "viewer-fullscreen:pseudo_off:" + String(n);
        }

        if (exitFullscreen) {
          try {
            exitFullscreen.call(document);
          } catch (e) {
            return "viewer-fullscreen:exit_error:" + String(n);
          }
        }

        return "viewer-fullscreen:native_off:" + String(n);
      }

      if (requestFullscreen && document.fullscreenEnabled !== false) {
        try {
          const result = requestFullscreen.call(panel);
          if (result && typeof result.catch === "function") {
            result.catch(function() {
              setPseudoFullscreen(true);
            });
          }
          return "viewer-fullscreen:native_on:" + String(n);
        } catch (e) {
          setPseudoFullscreen(true);
          return "viewer-fullscreen:pseudo_on:" + String(n);
        }
      }

      setPseudoFullscreen(true);
      return "viewer-fullscreen:pseudo_on:" + String(n);
    }
  }
});
