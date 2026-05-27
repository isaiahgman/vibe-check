const { createApp, ref, computed, onMounted } = Vue;

createApp({
    setup() {
        const SESSION_MINUTES = 25;
        const totalSeconds = SESSION_MINUTES * 60;
        
        const timeRemaining = ref(totalSeconds);
        const isRunning = ref(false);
        const totalFocusTime = ref(0);
        let timerInterval = null;

        const formattedTime = computed(() => {
            const minutes = Math.floor(timeRemaining.value / 60);
            const seconds = timeRemaining.value % 60;
            return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        });

        const fetchTotalTime = async () => {
            try {
                const response = await fetch('/api/focus');
                const data = await response.json();
                totalFocusTime.value = data.total_focus_time || 0;
            } catch (error) {
                console.error("Failed to fetch total time:", error);
            }
        };

        const saveSession = async () => {
            try {
                const response = await fetch('/api/focus', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ session_time: SESSION_MINUTES })
                });
                const data = await response.json();
                if (data.success) {
                    totalFocusTime.value = data.total_focus_time;
                }
            } catch (error) {
                console.error("Failed to save session:", error);
            }
        };

        const updateProgress = () => {
            const progress = timeRemaining.value / totalSeconds;
            const circumference = 2 * Math.PI * 140; // ~879.6
            const offset = circumference - progress * circumference;
            
            gsap.to('.progress-ring-circle', {
                strokeDashoffset: offset,
                duration: 1,
                ease: "linear"
            });
        };

        const tick = () => {
            if (timeRemaining.value > 0) {
                timeRemaining.value--;
                updateProgress();
            } else {
                stopTimer();
                saveSession();
                
                // Reset visual and state after finishing
                timeRemaining.value = totalSeconds;
                
                const circumference = 2 * Math.PI * 140;
                gsap.to('.progress-ring-circle', {
                    strokeDashoffset: 0,
                    duration: 1,
                    ease: "power2.out"
                });
            }
        };

        const toggleTimer = () => {
            if (isRunning.value) {
                stopTimer();
            } else {
                startTimer();
            }
        };

        const startTimer = () => {
            if (!isRunning.value) {
                isRunning.value = true;
                timerInterval = setInterval(tick, 1000);
            }
        };

        const stopTimer = () => {
            isRunning.value = false;
            clearInterval(timerInterval);
        };

        const resetTimer = () => {
            stopTimer();
            timeRemaining.value = totalSeconds;
            
            const circumference = 2 * Math.PI * 140;
            gsap.to('.progress-ring-circle', {
                strokeDashoffset: 0,
                duration: 0.5,
                ease: "power2.out"
            });
        };

        const setupMouseTracking = () => {
            window.addEventListener('mousemove', (e) => {
                const mouseX = e.clientX / window.innerWidth;
                const mouseY = e.clientY / window.innerHeight;
                
                document.documentElement.style.setProperty('--mouse-x', mouseX);
                document.documentElement.style.setProperty('--mouse-y', mouseY);
            });
        };

        const setupMagneticButtons = () => {
            const buttons = document.querySelectorAll('.magnetic-btn');
            
            buttons.forEach(btn => {
                const span = btn.querySelector('span');
                
                btn.addEventListener('mousemove', (e) => {
                    const rect = btn.getBoundingClientRect();
                    const x = e.clientX - rect.left - rect.width / 2;
                    const y = e.clientY - rect.top - rect.height / 2;
                    
                    gsap.to(btn, {
                        x: x * 0.4,
                        y: y * 0.4,
                        duration: 0.3,
                        ease: "power2.out"
                    });
                    
                    if (span) {
                        gsap.to(span, {
                            x: x * 0.2,
                            y: y * 0.2,
                            duration: 0.3,
                            ease: "power2.out"
                        });
                    }
                });

                btn.addEventListener('mouseleave', () => {
                    gsap.to(btn, {
                        x: 0,
                        y: 0,
                        duration: 0.7,
                        ease: "elastic.out(1, 0.3)"
                    });
                    
                    if (span) {
                        gsap.to(span, {
                            x: 0,
                            y: 0,
                            duration: 0.7,
                            ease: "elastic.out(1, 0.3)"
                        });
                    }
                });
            });
        };

        onMounted(() => {
            fetchTotalTime();
            
            // Initialize progress ring offset
            const circle = document.querySelector('.progress-ring-circle');
            if (circle) {
                const circumference = 2 * Math.PI * 140;
                circle.style.strokeDasharray = `${circumference} ${circumference}`;
                circle.style.strokeDashoffset = '0';
            }
            
            setupMouseTracking();
            setupMagneticButtons();
        });

        return {
            timeRemaining,
            isRunning,
            totalFocusTime,
            formattedTime,
            toggleTimer,
            resetTimer
        };
    }
}).mount('#app');
