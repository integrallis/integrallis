// Integrallis - Main JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // Particles Animation (Pusher-style)
    // ==========================================
    const canvas = document.getElementById('particles-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        let animationId;

        // Configuration
        const config = {
            particleCount: 100,
            particleSize: 2.5,
            lineDistance: 180,
            particleSpeed: 0.4,
            particleColor: 'rgba(255, 90, 54, 0.8)',
            lineColor: 'rgba(255, 90, 54, 0.2)',
            mouseRadius: 200,
            mouseForce: 0.02
        };

        let mouse = { x: null, y: null };

        // Resize canvas
        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        // Particle class
        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.vx = (Math.random() - 0.5) * config.particleSpeed;
                this.vy = (Math.random() - 0.5) * config.particleSpeed;
                this.size = Math.random() * config.particleSize + 1;
            }

            update() {
                // Mouse interaction
                if (mouse.x !== null && mouse.y !== null) {
                    const dx = mouse.x - this.x;
                    const dy = mouse.y - this.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < config.mouseRadius) {
                        const force = (config.mouseRadius - distance) / config.mouseRadius;
                        this.vx -= (dx / distance) * force * config.mouseForce;
                        this.vy -= (dy / distance) * force * config.mouseForce;
                    }
                }

                // Apply velocity
                this.x += this.vx;
                this.y += this.vy;

                // Boundary check with wrapping
                if (this.x < 0) this.x = canvas.width;
                if (this.x > canvas.width) this.x = 0;
                if (this.y < 0) this.y = canvas.height;
                if (this.y > canvas.height) this.y = 0;

                // Damping
                this.vx *= 0.99;
                this.vy *= 0.99;

                // Maintain minimum velocity
                const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
                if (speed < config.particleSpeed * 0.5) {
                    this.vx += (Math.random() - 0.5) * 0.1;
                    this.vy += (Math.random() - 0.5) * 0.1;
                }
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = config.particleColor;
                ctx.fill();
            }
        }

        // Initialize particles
        function initParticles() {
            particles = [];
            for (let i = 0; i < config.particleCount; i++) {
                particles.push(new Particle());
            }
        }

        // Draw connections between nearby particles
        function drawConnections() {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < config.lineDistance) {
                        const opacity = 1 - (distance / config.lineDistance);
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(255, 90, 54, ${opacity * 0.25})`;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }
            }
        }

        // Animation loop
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particles.forEach(particle => {
                particle.update();
                particle.draw();
            });

            drawConnections();
            animationId = requestAnimationFrame(animate);
        }

        // Event listeners
        window.addEventListener('resize', () => {
            resizeCanvas();
            initParticles();
        });

        window.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });

        window.addEventListener('mouseout', () => {
            mouse.x = null;
            mouse.y = null;
        });

        // Initialize
        resizeCanvas();
        initParticles();
        animate();
    }

    // ==========================================
    // Navigation
    // ==========================================
    const nav = document.querySelector('.nav');

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        if (currentScroll > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offset = 80;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ==========================================
    // Scroll Reveal Animation
    // ==========================================
    const revealElements = document.querySelectorAll('.reveal');

    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const revealPoint = 150;

        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            if (elementTop < windowHeight - revealPoint) {
                element.classList.add('visible');
            }
        });
    };

    revealOnScroll();

    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                revealOnScroll();
                ticking = false;
            });
            ticking = true;
        }
    });

    // ==========================================
    // Hero Background Effects
    // ==========================================
    const heroBg = document.querySelector('.hero-bg');
    if (heroBg) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            heroBg.style.transform = `translateY(${scrolled * 0.3}px)`;
        });
    }

    const hero = document.querySelector('.hero');
    if (hero && heroBg) {
        hero.addEventListener('mousemove', (e) => {
            const { clientX, clientY } = e;
            const { width, height, left, top } = hero.getBoundingClientRect();

            const x = (clientX - left) / width - 0.5;
            const y = (clientY - top) / height - 0.5;

            heroBg.style.background = `
                radial-gradient(ellipse 80% 50% at ${50 + x * 20}% ${-20 + y * 20}%, rgba(255, 90, 54, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at ${80 + x * 10}% ${60 + y * 10}%, rgba(255, 90, 54, 0.05) 0%, transparent 50%)
            `;
        });
    }

    // ==========================================
    // Card Hover Effects
    // ==========================================
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const { width, height, left, top } = card.getBoundingClientRect();
            const x = (e.clientX - left) / width - 0.5;
            const y = (e.clientY - top) / height - 0.5;

            card.style.transform = `
                perspective(1000px)
                rotateY(${x * 5}deg)
                rotateX(${-y * 5}deg)
                translateY(-4px)
            `;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });

    // ==========================================
    // Console Easter Egg
    // ==========================================
    console.log('%c Integrallis ', 'background: linear-gradient(135deg, #ff7a3d 0%, #ff0000 100%); color: white; font-size: 20px; padding: 10px; border-radius: 4px;');
    console.log('%cArtificial Intelligence・Applied', 'color: #71717a; font-size: 14px;');
    console.log('%cInterested? info@integrallis.com', 'color: #ff5a36; font-size: 12px;');
});
