const { createApp, ref, onMounted } = Vue;

const App = {
    setup() {
        const isDarkMode = ref(localStorage.getItem('theme') === 'dark');
        
        // Initial setup for theme
        if (isDarkMode.value) document.documentElement.setAttribute('data-theme', 'dark');

        const toggleTheme = () => {
            isDarkMode.value = !isDarkMode.value;
            const theme = isDarkMode.value ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        };

        const tasks = ref([
            'Review PR #42',
            'Update Vue components',
            'Write documentation'
        ]);
        const newTask = ref('');

        const sessions = ref([
            { title: 'Morning Sprint', date: 'Oct 24, 9:00 AM', status: 'Completed' },
            { title: 'Bug Fixing', date: 'Oct 24, 1:00 PM', status: 'Active' },
            { title: 'Code Review', date: 'Oct 24, 3:30 PM', status: 'Pending' },
            { title: 'Planning Phase', date: 'Oct 25, 10:00 AM', status: 'Pending' }
        ]);

        const addTask = () => {
            if (newTask.value.trim()) {
                tasks.value.push(newTask.value.trim());
                newTask.value = '';
            }
        };

        const deleteTask = (index, event) => {
            const el = event.currentTarget.closest('.task-card');
            if (el) {
                // Add a "pop" exit animation
                gsap.to(el, {
                    scale: 1.1,
                    opacity: 0,
                    duration: 0.2,
                    ease: "back.in(1.7)",
                    onComplete: () => {
                        tasks.value.splice(index, 1);
                    }
                });
            } else {
                tasks.value.splice(index, 1);
            }
        };

        // 3D Parallax Tilt Effect for Cards
        const tiltEffect = (event) => {
            const el = event.currentTarget;
            const rect = el.getBoundingClientRect();
            
            // Mouse position relative to the element
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // Center of the element
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Calculate rotation (max 15 degrees)
            const rotateX = ((y - centerY) / centerY) * -15;
            const rotateY = ((x - centerX) / centerX) * 15;
            
            gsap.to(el, {
                rotationX: rotateX,
                rotationY: rotateY,
                transformPerspective: 1000,
                ease: 'power1.out',
                duration: 0.4
            });
        };

        // Reset Tilt when mouse leaves
        const resetTilt = (event) => {
            const el = event.currentTarget;
            gsap.to(el, {
                rotationX: 0,
                rotationY: 0,
                ease: 'power3.out',
                duration: 0.6
            });
        };

        onMounted(() => {
            const cursor = document.getElementById('custom-cursor');
            
            // Start cursor offscreen
            gsap.set(cursor, { x: -100, y: -100 });

            // Make cursor follow mouse with a trailing delay and update wave background
            window.addEventListener('mousemove', (e) => {
                // Update CSS variables for wave background
                document.documentElement.style.setProperty('--mouse-x', `${(e.clientX / window.innerWidth) * 100}%`);
                document.documentElement.style.setProperty('--mouse-y', `${(e.clientY / window.innerHeight) * 100}%`);

                const isClickable = e.target.closest('button, input, .card');
                
                gsap.to(cursor, {
                    x: e.clientX,
                    y: e.clientY,
                    scale: isClickable ? 1.5 : 1,
                    opacity: isClickable ? 0.8 : 1,
                    duration: 0.15, // Creates the trailing effect
                    ease: "power2.out"
                });
            });
        });

        return {
            isDarkMode,
            toggleTheme,
            tasks,
            newTask,
            sessions,
            addTask,
            deleteTask,
            tiltEffect,
            resetTilt
        };
    }
};

createApp(App).mount('#app');
