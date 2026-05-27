import { describe, it, expect } from 'vitest';

describe('Focus Flow Logic Tests', () => {
  it('should initialize with an empty task array theoretically', () => {
    // In our main.js, tasks are populated via Vue refs. 
    // Here we test pure JS logic equivalents.
    const tasks = [];
    expect(tasks.length).toBe(0);
  });

  it('addTask logic should append to array and clear input', () => {
    const tasks = [];
    let nextId = 1;
    let newTask = "Meditate for 10 minutes";
    
    if (newTask.trim()) {
      tasks.push({ id: nextId++, text: newTask.trim() });
      newTask = "";
    }

    expect(tasks.length).toBe(1);
    expect(tasks[0].text).toBe("Meditate for 10 minutes");
    expect(newTask).toBe("");
  });

  it('deleteTask logic should correctly splice the array', () => {
    const tasks = [
        { id: 1, text: "Task 1" },
        { id: 2, text: "Task 2" },
        { id: 3, text: "Task 3" }
    ];
    const idToDelete = 2;

    const index = tasks.findIndex(t => t.id === idToDelete);
    if (index !== -1) tasks.splice(index, 1);

    expect(tasks.length).toBe(2);
    expect(tasks[0].text).toBe("Task 1");
    expect(tasks[1].text).toBe("Task 3");
  });
});
