import express from 'express';
import { query } from '../utils/dbUtils';
import { redis } from '../utils/redisUtils';

const router = express.Router();

router.get('/feeds', async (_req, res) => {
  try {
    const result = await query('SELECT * FROM feeds LIMIT 10');
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

router.get('/items', async (_req, res) => {
  try {
    const start = performance.now();
    const result = await query('SELECT * FROM items LIMIT 10');
    const end = performance.now();
    const took = end - start;
    res.json({ result, "time": took });
    console.log(`Query took ${took}ms`);
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});


router.get('/random-items/:feedId', async (req, res) => {
  try {
    const start = performance.now();
    const feedId = parseInt(req.params.feedId, 10);
    const result = await query('SELECT * FROM items WHERE feed_id = $1', [feedId]);
    const end = performance.now();
    const took = end - start;
    res.json({ result, "time": took });
    console.log(`Uncached Query took ${took}ms`);
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

router.get('/random-items-cached/:feedId', async (req, res) => {
  const start = performance.now();
  const feedId = parseInt(req.params.feedId, 10);
  const cacheKey = `item-${feedId}`;
  let end: number, time: number;

  try {
    const cached = await redis.get(cacheKey);
    if (cached) {
      const result = JSON.parse(cached);
      end = performance.now();
      time = end - start;
      res.json({ result, time });
      console.log(`Cached Query took ${time}ms`);
      return
    }
    const result = await query('SELECT * FROM items WHERE feed_id = $1', [feedId]);
    end = performance.now();
    await redis.setex(cacheKey, 300, JSON.stringify(result));
    time = end - start;
    res.json({ result, time });
    console.log(`Uncached Query took ${time}ms`);
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

export default router;

