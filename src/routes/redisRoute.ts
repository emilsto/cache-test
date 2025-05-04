import express from 'express';
import { redis } from '../utils/redisUtils';

const router = express.Router();

router.get('/get/:key', async (req, res) => {
  const key = req.params.key;
  try {
    const value = await redis.get(key);
    res.json({ key, value });
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

router.post('/set', async (req, res) => {
  const { key, value } = req.body;
  try {
    await redis.set(key, value);
    res.json({ message: 'Key-value set successfully' });
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

export default router;
