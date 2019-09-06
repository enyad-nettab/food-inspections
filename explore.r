data <- read.csv('exploratory_data.csv')

model <- glm(bad_now ~ pct_bad_previous + as.factor(inspection_authority), data = data, family = "binomial")
summary(model)

exp(1.50354)
