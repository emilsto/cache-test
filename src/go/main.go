package main

import (
	"log"

	"context"
	"github.com/emilsto/cache-test/routes"
	"github.com/emilsto/cache-test/utils"
	"github.com/gofiber/fiber/v2"
)

func main() {
	ctx := context.Background()

	store, err := utils.NewStore(ctx)
	if err != nil {
		log.Fatal("Failed to connect to postgres")
	}

	cache := utils.NewCache()

	handler := &routes.Handler{Store: store, Cache: cache}

	log.Print(cache, store)

	app := fiber.New()

	app.Get("/", routes.Health)
	app.Get("/random-items/:feedId", handler.UncachedRoute)
	app.Get("/random-items-cached/:feedId", handler.CachedRoute)

	log.Fatal(app.Listen(":3001"))
}
