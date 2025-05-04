import { Pool } from 'pg';

const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'mydatabase',
  password: 'postgres',
  port: 5432,
});

export const query = async (text: string, params?: any[]) => {
  const res = await pool.query(text, params);
  return res.rows;
};

