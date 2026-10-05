/**
 * Baseline Express API Server (Uncached)
 * Fetches directly from upstream API on every request.
 */

const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
    res.json({ status: "healthy", caching: false });
});

app.get("/photos", async (req, res) => {
    try {
        const { albumId } = req.query;
        const config = albumId ? { params: { albumId } } : {};
        const { data } = await axios.get("https://jsonplaceholder.typicode.com/photos", config);
        res.json(data);
    } catch (err) {
        res.status(err.response?.status || 500).json({ error: err.message });
    }
});

app.get("/photos/:id", async (req, res) => {
    try {
        const { id } = req.params;
        const { data } = await axios.get(`https://jsonplaceholder.typicode.com/photos/${id}`);
        res.json(data);
    } catch (err) {
        res.status(err.response?.status || 500).json({ error: err.message });
    }
});

if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`[Uncached Server] Running on http://localhost:${PORT}`);
    });
}

module.exports = app;
