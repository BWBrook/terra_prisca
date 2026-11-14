# Ocean fraction of each 10-degree latitude circle (80N..80S), the l'/l1 of
# Sellers (1969) eq. (13), from the R `maps` world coastline (maps::map.where).
# Also the band mean over +-5 degrees, as an alternative reading, and the
# area-weighted ocean fraction of each 10-degree belt (for Table 3's land heating).
#   Rscript src/terra_prisca/budyko_sellers/data/ocean_fraction.R
suppressMessages(library(maps))
lon <- seq(-179.95, 179.95, by = 0.1)
frac <- function(lat) mean(is.na(map.where("world", lon, rep(lat, length(lon)))))
circles <- seq(80, -80, by = -10)
band <- function(c) mean(sapply(seq(c - 4.75, c + 4.75, by = 0.5), frac))
out <- data.frame(latitude = circles,
                  ocean_circle = round(sapply(circles, frac), 4),
                  ocean_band = round(sapply(circles, band), 4))
write.csv(out, "src/terra_prisca/budyko_sellers/data/ocean_fraction.csv", row.names = FALSE, quote = FALSE)
print(out)
belts <- seq(85, -85, by = -10)
belt <- data.frame(latitude = belts, ocean_belt = round(sapply(belts, function(c) {
  la <- seq(c - 4.95, c + 4.95, by = 0.1)
  sum(sapply(la, frac) * cos(la * pi / 180)) / sum(cos(la * pi / 180))
}), 4))
write.csv(belt, "src/terra_prisca/budyko_sellers/data/ocean_fraction_belts.csv", row.names = FALSE, quote = FALSE)
print(belt)
