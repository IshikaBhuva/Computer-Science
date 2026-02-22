const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());

// Serve frontend
app.use(express.static(path.join(__dirname)));

// --------------------
// In-memory database
// --------------------
let users = [];

let groups = [
  { id: 1, name: "Data Structures Study", course: "CS201", desc: "Weekly review of Trees and Graphs.", members: 4, limit: 6 },
  { id: 2, name: "Econ Paper Prep", course: "ECON10", desc: "Analyzing global trade trends.", members: 2, limit: 5 },
  { id: 3, name: "MCAT Flashcards", course: "MED400", desc: "Intense daily quiz sessions.", members: 9, limit: 10 },
  { id: 4, name: "Modern Lit Discussion", course: "ENG302", desc: "Post-modern novel analysis.", members: 3, limit: 4 }
];

// --------------------
// AUTH
// --------------------
app.post('/login', (req, res) => {
  const { name, uni } = req.body;

  if (!name || !uni) {
    return res.status(400).json({ error: "Missing name or university" });
  }

  const user = {
    id: Date.now(),
    name,
    uni,
    courses: [],
    joinedGroups: [],
    requests: []
  };

  users.push(user);
  res.json(user);
});

// --------------------
// COURSE MANAGEMENT
// --------------------
app.post('/course', (req, res) => {
  const { userId, course } = req.body;

  const user = users.find(u => u.id === userId);
  if (!user) return res.status(404).json({ error: "User not found" });

  if (!user.courses.includes(course)) {
    user.courses.push(course);
  }

  res.json(user.courses);
});

app.post('/course/remove', (req, res) => {
  const { userId, course } = req.body;

  const user = users.find(u => u.id === userId);
  if (!user) return res.status(404).json({ error: "User not found" });

  user.courses = user.courses.filter(c => c !== course);

  res.json(user.courses);
});

// --------------------
// GROUPS
// --------------------
app.get('/groups', (req, res) => {
  res.json(groups);
});

// Create group
app.post('/groups', (req, res) => {
  const { name, course, desc, userId } = req.body;

  if (!name || !course || !desc || !userId) {
    return res.status(400).json({ error: "Missing data" });
  }

  const newGroup = {
    id: Date.now(),
    name,
    course,
    desc,
    members: 1,
    limit: 10
  };

  groups.unshift(newGroup);

  const user = users.find(u => u.id === userId);
  if (user && !user.joinedGroups.includes(newGroup.id)) {
    user.joinedGroups.push(newGroup.id);
  }

  res.json(newGroup);
});

// --------------------
// JOIN GROUP (FIXED)
// --------------------
app.post('/groups/join', (req, res) => {
  const { userId, groupId } = req.body;

  const user = users.find(u => u.id === userId);
  const group = groups.find(g => g.id === groupId);

  if (!user || !group) {
    return res.status(404).json({ error: "User or group not found" });
  }

  // Already joined
  if (user.joinedGroups.includes(groupId)) {
    return res.json(user);
  }

  // Check capacity
  if (group.members >= group.limit) {
    return res.status(400).json({ error: "Group is full" });
  }

  // Add to joined immediately
  user.joinedGroups.push(groupId);

  // Remove from pending if somehow exists
  user.requests = user.requests.filter(r => r !== groupId);

  // Increase member count
  group.members += 1;

  // Return fully updated user
  res.json(user);
});

// --------------------
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
