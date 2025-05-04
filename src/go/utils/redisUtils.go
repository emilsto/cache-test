package utils

import (
	"context"
	"github.com/redis/go-redis/v9"
	"log"
	"time"
)

type Cache struct {
	Client *redis.Client
}

func NewCache() (c *Cache) {
	client := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "",
		DB:       0,
		Protocol: 2,
	})
	log.Print("Cache connnection established succesfully")

	return &Cache{Client: client}
}

func (c *Cache) Close() {
	if c.Client != nil {
		err := c.Client.Close()
		if err != nil {
			log.Printf("Error closing Redis client: %v", err)
		} else {
			log.Println("Redis client closed")
		}
	}
}

func (c *Cache) Get(ctx context.Context, key string) (string, error) {
	cmd := c.Client.Get(ctx, key)
	return cmd.Result()
}

func (c *Cache) Set(ctx context.Context, key string, value any, expiration time.Duration) error {
	cmd := c.Client.Set(ctx, key, value, expiration)
	return cmd.Err()
}
