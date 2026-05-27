const { createApp, ref, onMounted } = Vue;

const App = {
    setup() {
        const isDarkMode = ref(localStorage.getItem('theme') === 'dark');
        
        // Initial setup for Tailwind's class-based dark mode
        if (isDarkMode.value) document.documentElement.classList.add('dark');

        const toggleTheme = () => {
            isDarkMode.value = !isDarkMode.value;
            const theme = isDarkMode.value ? 'dark' : 'light';
            
            if (isDarkMode.value) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
            
            localStorage.setItem('theme', theme);
        };

        const tasks = ref([
            { id: 1, text: 'Review PR #42' },
            { id: 2, text: 'Update Vue components' },
            { id: 3, text: 'Write documentation' }
        ]);
        let nextId = 4;
        const newTask = ref('');

        const sessions = ref([
            { title: 'Morning Sprint', date: 'Oct 24, 9:00 AM', status: 'Completed' },
            { title: 'Bug Fixing', date: 'Oct 24, 1:00 PM', status: 'Active' },
            { title: 'Code Review', date: 'Oct 24, 3:30 PM', status: 'Pending' },
            { title: 'Planning Phase', date: 'Oct 25, 10:00 AM', status: 'Pending' }
        ]);

        const addTask = () => {
            if (newTask.value.trim()) {
                tasks.value.push({ id: nextId++, text: newTask.value.trim() });
                newTask.value = '';
            }
        };

        const deleteTask = (id) => {
            const index = tasks.value.findIndex(t => t.id === id);
            if (index !== -1) tasks.value.splice(index, 1);
        };

        // 3D Tilt Effect applied to elements with .card class
        const tiltEffect = (e, card) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = ((y - centerY) / centerY) * -10; // Max 10 deg rotation
            const rotateY = ((x - centerX) / centerX) * 10;
            
            gsap.to(card, {
                rotateX: rotateX,
                rotateY: rotateY,
                transformPerspective: 1000,
                duration: 0.4,
                ease: "power2.out"
            });
        };

        const resetTilt = (card) => {
            gsap.to(card, {
                rotateX: 0,
                rotateY: 0,
                duration: 0.6,
                ease: "power2.out"
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

            // Bind tilt effects to all cards
            document.querySelectorAll('.card').forEach(card => {
                card.addEventListener('mousemove', (e) => tiltEffect(e, card));
                card.addEventListener('mouseleave', () => resetTilt(card));
            });
        });

        return {
            isDarkMode,
            toggleTheme,
            tasks,
            newTask,
            sessions,
            addTask,
            deleteTask
        };
    }
};

createApp(App).mount('#app');
