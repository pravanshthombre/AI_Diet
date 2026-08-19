const charts = {
    drawProgressRing(canvasId, percent, color, labelText) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        // Use fixed display size from HTML attributes (prevents runaway scaling)
        const displayWidth = 90;
        const displayHeight = 90;

        // Lock CSS size so the canvas never visually grows on re-render
        canvas.style.width = displayWidth + 'px';
        canvas.style.height = displayHeight + 'px';

        // Set internal resolution for sharp rendering on high-DPI screens
        const dpr = window.devicePixelRatio || 1;
        canvas.width = displayWidth * dpr;
        canvas.height = displayHeight * dpr;

        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);

        const cx = displayWidth / 2;
        const cy = displayHeight / 2;
        const radius = Math.min(cx, cy) - 9;
        
        ctx.clearRect(0, 0, displayWidth, displayHeight);
        
        // Background track
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
        ctx.lineWidth = 7;
        ctx.strokeStyle = '#e2e8e5';
        ctx.stroke();

        // Progress arc
        const startAngle = -0.5 * Math.PI;
        const clampedPct = Math.min(100, Math.max(0, percent));
        const endAngle = startAngle + (clampedPct / 100) * 2 * Math.PI;
        
        if (clampedPct > 0) {
            ctx.beginPath();
            ctx.arc(cx, cy, radius, startAngle, endAngle);
            ctx.lineWidth = 7;
            ctx.lineCap = 'round';
            ctx.strokeStyle = color;
            ctx.stroke();
        }

        // Percentage text
        ctx.fillStyle = '#0f172a';
        ctx.font = '700 13px Plus Jakarta Sans, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${Math.round(percent)}%`, cx, cy);
    },

    drawGauge(canvasId, value, min, max, labelText) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // Use fixed display size
        const displayWidth = 90;
        const displayHeight = 50;

        // Lock CSS size
        canvas.style.width = displayWidth + 'px';
        canvas.style.height = displayHeight + 'px';

        // Set internal resolution for high-DPI
        const dpr = window.devicePixelRatio || 1;
        canvas.width = displayWidth * dpr;
        canvas.height = displayHeight * dpr;

        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);

        const cx = displayWidth / 2;
        const cy = displayHeight - 6;
        const radius = Math.min(cx, cy) - 6;
        
        ctx.clearRect(0, 0, displayWidth, displayHeight);

        // Track
        ctx.beginPath();
        ctx.arc(cx, cy, radius, Math.PI, 2 * Math.PI);
        ctx.lineWidth = 8;
        ctx.strokeStyle = '#e2e8e5';
        ctx.stroke();

        // Clamp value
        const clampedVal = Math.max(min, Math.min(max, value || 22));
        const ratio = (clampedVal - min) / (max - min);
        const endAngle = Math.PI + ratio * Math.PI;

        // Color based on BMI standard
        let color = '#10b981'; // Normal
        if (value < 18.5) color = '#f59e0b'; // Underweight
        if (value >= 25 && value < 30) color = '#f97316'; // Overweight
        if (value >= 30) color = '#ef4444'; // Obese

        ctx.beginPath();
        ctx.arc(cx, cy, radius, Math.PI, endAngle);
        ctx.lineWidth = 8;
        ctx.lineCap = 'round';
        ctx.strokeStyle = color;
        ctx.stroke();
    },

    drawLineChart(canvasId, dataPoints, labels) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // For line chart: use container width (responsive), but fixed height
        const displayWidth = canvas.parentElement ? canvas.parentElement.clientWidth - 20 : 300;
        const displayHeight = 150;

        // Lock CSS size
        canvas.style.width = displayWidth + 'px';
        canvas.style.height = displayHeight + 'px';

        // Set internal resolution for high-DPI
        const dpr = window.devicePixelRatio || 1;
        canvas.width = displayWidth * dpr;
        canvas.height = displayHeight * dpr;

        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, displayWidth, displayHeight);
        
        if (!dataPoints || dataPoints.length === 0) {
            ctx.fillStyle = '#94a3b8';
            ctx.font = '12px Plus Jakarta Sans, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No history logged yet', displayWidth / 2, displayHeight / 2);
            return;
        }

        const paddingX = 24;
        const paddingY = 20;
        const width = displayWidth - paddingX * 2;
        const height = displayHeight - paddingY * 2;
        
        const min = Math.min(...dataPoints) - 1;
        const max = Math.max(...dataPoints) + 1;
        const range = max - min || 1;
        
        // Draw Subtle Grid line
        ctx.strokeStyle = '#f1f5f3';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(paddingX, displayHeight - paddingY);
        ctx.lineTo(displayWidth - paddingX, displayHeight - paddingY);
        ctx.stroke();

        const stepX = width / Math.max(1, (dataPoints.length - 1));

        // Area Gradient Fill
        const gradient = ctx.createLinearGradient(0, paddingY, 0, displayHeight - paddingY);
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

        ctx.beginPath();
        dataPoints.forEach((val, i) => {
            const x = paddingX + i * stepX;
            const y = displayHeight - paddingY - ((val - min) / range) * height;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.lineTo(paddingX + (dataPoints.length - 1) * stepX, displayHeight - paddingY);
        ctx.lineTo(paddingX, displayHeight - paddingY);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Draw Line
        ctx.beginPath();
        ctx.strokeStyle = '#059669';
        ctx.lineWidth = 2.5;
        ctx.lineJoin = 'round';
        
        dataPoints.forEach((val, i) => {
            const x = paddingX + i * stepX;
            const y = displayHeight - paddingY - ((val - min) / range) * height;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Draw Dot Points & Values
        dataPoints.forEach((val, i) => {
            const x = paddingX + i * stepX;
            const y = displayHeight - paddingY - ((val - min) / range) * height;
            
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = '#064e3b';
            ctx.fill();
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();

            // Label
            if (labels && labels[i]) {
                ctx.fillStyle = '#64748b';
                ctx.font = '10px Plus Jakarta Sans, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(labels[i], x, displayHeight - 4);
            }
        });
    }
};

window.charts = charts;
