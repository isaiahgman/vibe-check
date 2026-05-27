const { createApp, ref, onMounted } = Vue;
const { createVuetify } = Vuetify;

const vuetify = createVuetify();

const App = {
    setup() {
        const isDarkMode = ref(localStorage.getItem('theme') === 'dark');

        const toggleTheme = () => {
            isDarkMode.value = !isDarkMode.value;
            localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light');
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

        const getStatusColor = (status) => {
            if (status.toLowerCase() === 'completed') return 'success';
            if (status.toLowerCase() === 'active') return 'primary';
            return 'warning';
        };

        const addTask = () => {
            if (newTask.value.trim()) {
                tasks.value.push(newTask.value.trim());
                newTask.value = '';
            }
        };

        const deleteTask = (index) => {
            tasks.value.splice(index, 1);
        };

        onMounted(() => {
            const cursor = document.getElementById('custom-cursor');
            gsap.set(cursor, { x: -100, y: -100 });

            window.addEventListener('mousemove', (e) => {
                const isClickable = e.target.closest('button, input, .v-card, .v-btn');
                
                gsap.to(cursor, {
                    x: e.clientX,
                    y: e.clientY,
                    scale: isClickable ? 1.5 : 1,
                    opacity: isClickable ? 0.8 : 1,
                    duration: 0.15,
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
            getStatusColor
        };
    }
};

createApp(App).use(vuetify).mount('#app');
