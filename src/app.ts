import express from 'express';
import server from './server';

const app = express();
app.use(server);
export { app };
