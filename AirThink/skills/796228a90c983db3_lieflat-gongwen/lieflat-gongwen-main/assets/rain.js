
(function(){
  function setup(canvas){
    const ctx = canvas.getContext("2d");
    let width = 0, height = 0, drops = [], ripples = [];
    function makeDrop(seed){
      return {
        x: Math.random() * (width + 160) - 80,
        y: seed ? Math.random() * height : -30 - Math.random() * 180,
        len: 12 + Math.random() * 15,
        speed: 2.7 + Math.random() * 2.4,
        opacity: 0.22 + Math.random() * 0.36,
        width: 0.45 + Math.random() * 0.45
      };
    }
    function resize(){
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width; height = rect.height;
      canvas.width = width * dpr; canvas.height = height * dpr;
      canvas.style.width = width + "px"; canvas.style.height = height + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      drops = [];
      const count = Math.min(220, Math.floor(95 + (width * height) / 5800));
      for (let i = 0; i < count; i += 1) drops.push(makeDrop(true));
    }
    function spawnRipple(x){
      ripples.push({ x, y: height - 10 - Math.random() * 34, age: 0, life: 90 + Math.random() * 58, maxR: 14 + Math.random() * 22 });
    }
    let last = performance.now();
    function frame(){
      const now = performance.now();
      const dt = Math.min((now - last) / 16.66, 2);
      last = now;
      ctx.clearRect(0, 0, width, height);
      ctx.lineCap = "round";
      for (let i = drops.length - 1; i >= 0; i -= 1) {
        const d = drops[i];
        d.y += d.speed * dt; d.x += d.speed * 0.11 * dt;
        const x0 = d.x - d.len * 0.11;
        const y0 = d.y - d.len;
        const grad = ctx.createLinearGradient(x0, y0, d.x, d.y);
        grad.addColorStop(0, "rgba(100,120,148," + (d.opacity * 0.25).toFixed(3) + ")");
        grad.addColorStop(0.4, "rgba(82,118,142," + d.opacity.toFixed(3) + ")");
        grad.addColorStop(1, "rgba(82,118,142," + (d.opacity * 0.42).toFixed(3) + ")");
        ctx.strokeStyle = grad; ctx.lineWidth = d.width;
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(d.x, d.y); ctx.stroke();
        if (d.y >= height - 4) {
          if (Math.random() < 0.3) spawnRipple(d.x);
          drops[i] = makeDrop(false);
        }
      }
      for (let i = ripples.length - 1; i >= 0; i -= 1) {
        const r = ripples[i];
        r.age += dt;
        const t = r.age / r.life;
        if (t >= 1) { ripples.splice(i, 1); continue; }
        const rad = r.maxR * (1 - Math.pow(1 - t, 2));
        const alpha = (1 - t) * (1 - t) * 0.55;
        ctx.strokeStyle = "rgba(80,108,136," + alpha.toFixed(3) + ")";
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.ellipse(r.x, r.y, rad, rad * 0.32, 0, 0, Math.PI * 2); ctx.stroke();
      }
      requestAnimationFrame(frame);
    }
    resize(); window.addEventListener("resize", resize); frame();
  }
  document.querySelectorAll(".rain").forEach(setup);
})();
