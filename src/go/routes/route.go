package routes

import (
	"fmt"
	"github.com/emilsto/cache-test/utils"
	"github.com/gofiber/fiber/v2"
	"github.com/json-iterator/go"
	"github.com/redis/go-redis/v9"

	"log"
	"strconv"
	"time"
)

type Handler struct {
	Store *utils.Store
	Cache *utils.Cache
}

func Health(c *fiber.Ctx) error {
	return c.JSON(map[string]any{
		"message": "ok",
	})
}

var json = jsoniter.ConfigCompatibleWithStandardLibrary

func (h *Handler) UncachedRoute(c *fiber.Ctx) error {
	start := time.Now()

	feedIDStr := c.Params("feedId")
	feedID, err := strconv.Atoi(feedIDStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid feedId parameter",
		})
	}

	result, err := h.Store.GetItemsByFeedID(c.Context(), feedID)
	if err != nil {
		log.Printf("Database Error: %v", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Database query failed",
		})
	}

	took := time.Since(start)
	log.Printf("Uncached Query took %s", took)

	return c.JSON(fiber.Map{
		"result": result,
		"time":   took.Milliseconds(),
	})
}

func (h *Handler) CachedRoute(c *fiber.Ctx) error {
	start := time.Now()

	feedIDStr := c.Params("feedId")
	feedID, err := strconv.Atoi(feedIDStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid feedId parameter",
		})
	}

	cacheKey := fmt.Sprintf("item-%d", feedID)
	var result []map[string]any
	var took time.Duration

	cached, err := h.Cache.Get(c.Context(), cacheKey)
	if err == nil {
		err = json.Unmarshal([]byte(cached), &result)
		if err != nil {
			log.Printf("Cache Unmarshal Error for key %s: %v. Fetching from DB instead.", cacheKey, err)
		} else {
			took = time.Since(start)
			log.Printf("Cached Query took %s", took)
			return c.JSON(fiber.Map{
				"result": result,
				"time":   took.Milliseconds(),
			})
		}
	} else if err != redis.Nil {
		log.Printf("Redis Get Error for key %s: %v. Attempting DB fetch.", cacheKey, err)
	}

	result, err = h.Store.GetItemsByFeedID(c.Context(), feedID)
	if err != nil {
		log.Printf("Database Error on Cache Miss: %v", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Database query failed after cache miss",
		})
	}

	took = time.Since(start)

	jsonResult, marshalErr := json.Marshal(result)
	if marshalErr != nil {
		log.Printf("Failed to marshal result for cache: %v", marshalErr)
	} else {
		cacheExpiration := 300 * time.Second
		setErr := h.Cache.Set(c.Context(), cacheKey, jsonResult, cacheExpiration)
		if setErr != nil {
			log.Printf("Failed to set cache key %s: %v", cacheKey, setErr)
		}
	}

	log.Printf("Uncached Query took %s", took)

	return c.JSON(fiber.Map{
		"result": result,
		"time":   took.Milliseconds(),
	})
}
