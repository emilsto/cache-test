import express from 'express';
import postgresRoute from './routes/postgresRoute';
import redisRoute from './routes/redisRoute';

const server = express();
server.use('/health', async (_req, res) => { res.json({ "message": "ok" }) });
server.use('/api/postgres', postgresRoute);
server.use('/api/redis', redisRoute);

const PORT = 3001;
server.listen(PORT, () => {
  console.log(`Server running on ${PORT}`);
});

export default server
