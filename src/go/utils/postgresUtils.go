package utils

import (
	"context"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"log"
)

type Store struct {
	DB *pgxpool.Pool
}

func NewStore(ctx context.Context) (*Store, error) {
	databaseURL := "postgres://postgres:postgres@localhost:5432/mydatabase?sslmode=disable"

	pool, err := pgxpool.New(ctx, databaseURL)
	if err != nil {
		return nil, fmt.Errorf("unable to create connection pool: %w", err)
	}

	err = pool.Ping(ctx)
	if err != nil {
		pool.Close()

		return nil, fmt.Errorf("unable to ping database: %w", err)
	}

	log.Println("Database connection pool established successfully")

	return &Store{DB: pool}, nil
}

func (s *Store) Close() {
	if s.DB != nil {
		s.DB.Close()
		log.Println("Database connection pool closed")
	}
}

func (s *Store) GetItemsByFeedID(ctx context.Context, feedID int) ([]map[string]any, error) {
	query := "SELECT * FROM items WHERE feed_id = $1"
	rows, err := s.DB.Query(ctx, query, feedID)
	if err != nil {
		return nil, fmt.Errorf("failed to query items for feed %d: %w", feedID, err)
	}
	defer rows.Close()

	var results []map[string]any
	fieldDescriptions := rows.FieldDescriptions()
	for rows.Next() {
		values, err := rows.Values()
		if err != nil {
			return nil, fmt.Errorf("failed to read row values: %w", err)
		}

		rowMap := make(map[string]any)
		for i, fd := range fieldDescriptions {
			colName := string(fd.Name)
			rowMap[colName] = values[i]
		}
		results = append(results, rowMap)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error during rows iteration: %w", err)
	}

	return results, nil
}
