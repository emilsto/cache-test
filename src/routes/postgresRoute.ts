import express from 'express';
import { query } from '../utils/dbUtils';
import { redis } from '../utils/redisUtils';

const router = express.Router();

router.get('/random-items/:feedId/:count', async (req, res) => {
  const start = performance.now();

  try {
    const feedId = parseInt(req.params.feedId, 10);
    const count = parseInt(req.params.count, 10);
    const result = await query('SELECT * FROM items WHERE feed_id = $1 ORDER BY RANDOM() LIMIT $2', [feedId, count]);
    const end = performance.now();
    const took = end - start;
    res.json({ result, took });
    console.log(`Postgres Query took ${took}ms`);
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

router.get('/random-items-cached/:feedId/:count', async (req, res) => {
  const start = performance.now();
  const feedId = parseInt(req.params.feedId, 10);
  const count = parseInt(req.params.count, 10);

  const cacheKey = `feed-items:${feedId}`;
  let end: number, took: number;

  try {
    let allFeedItems: any;
    const cached = await redis.get(cacheKey);

    if (cached) {
      allFeedItems = JSON.parse(cached);
      console.log(`Cache hit for feed ${feedId}. Items: ${allFeedItems.length}`);
    } else {
      console.log(`Cache miss for feed ${feedId}. Fetching from DB...`);
      allFeedItems = await query('SELECT * FROM items WHERE feed_id = $1', [feedId]);
      await redis.setex(cacheKey, 300, JSON.stringify(allFeedItems));
      console.log(`Fetched ${allFeedItems.length} items from DB and cached.`);
    }

    const shuffledItems = shuffleArray(allFeedItems);

    const result = shuffledItems.slice(0, count);

    end = performance.now();
    took = end - start;

    res.json({ result, took });

    console.log(`${cached ? 'Cached' : 'Uncached (DB fetch)'} process for feed ${feedId} took ${took}ms`);

  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

function shuffleArray(array: any[]) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

router.get('/random-redis-items/:feedId/:itemCount', async (req, res) => {
  const start = performance.now();

  try {
    const { feedId, itemCount } = req.params;
    const parsedItemCount = parseInt(itemCount, 10);
    const feedCacheKey = `feed:${feedId}:items`

    const sampledItems = await redis.srandmember(feedCacheKey, parsedItemCount);

    const pipeline = redis.multi();

    sampledItems.map((feedItemKey) => {
      pipeline.hgetall(feedItemKey);
    });

    const resolvedItems = await pipeline.exec();
    const end = performance.now();

    const processedItems = resolvedItems!.map(([error, itemData]) => {
      if (error) {
        return null;
      }
      return itemData;
    }).filter(item => item !== null);

    const took = end - start;
    res.json({ processedItems, took });
    console.log(`Redis Query took ${took}ms`);
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

export default router;

