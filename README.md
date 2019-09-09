# food-inspections
Load, explore, and make predictions with food inspection data...

## Initial comments
- The Vegas open data website seems to be broken. Anything I try to open 301-redirects me to their main transparency page. Proceeded with just NYC and Chicago.
- Opted to work with a CSV export, since integrating with the APIs would take additional time. However, this would obviously be the ideal way to keep data as fresh as possible.

## Schema and ETL
You'll find schema definitions in `schema.sql` and etl code in `etl.py`. The initial stab at the schema and ETL was to create separate tables for each city, and to unify them in a single view for ease of analyst use.

Chicago provided one record per inspection, with a list of violations crammed into a "violations" column in their data. New York provided one record per violation, so inspections were duplicated. New York also provided no identifier for the inspection, so I treated the establishment's identifier ("CAMIS") and inspection date as a unique key for the inspections, and generated my own ID.

The schema splits out inspections and violations, with a foreign key linking violations to their inspection. The ETL therefore does a bit of normalization work - splitting up violations from the single row for Chicago, and de-duping inspections for New York.

The view combines most of the data from each city, though there wasn't 100% overlap. The idea was to start making the data easier for an analyst to consume. Note that New York only appears to provide a grade for their regularly-scheduled inspections when it's an "A". Otherwise, there's no grade and a follow-up inspection appears to be scheduled. In order to make the data more useful, I went ahead and assigned the appropriate grade based on the score the restaurant was assigned. (Score -> grade mapping was determined through exploratory data analysis.) Also note that Chicago includes non-restaurant inspections, but I limited this view to restaurants only to keep the data more comparable.

There's a bunch of other work that could be done here. You could do a bunch more table normalization to reduce storage sizes and improve query performance. You could start coming up with some sort of unified data model that would allow data from each city to be more cleanly combined. I had plenty more ideas, but all was skipped in the interest of time.

## Exploratory data analysis

I did some brief exploratory analysis to answer a hypothesis I expected to be fairly obvious: restaurants with a checkered past would be more likely to get poor grades on their most recent inspection.

`exploratory_query.sql` pulls data to answer this question. It considers only routine inspections, and only the most commonly assigned grades/outcomes across the cities. It treats an inspection as "bad" if the score was less than the highest category (e.g., "B" and "C" are less than "A" and therefore "bad"), and "not bad" otherwise. Then, it calculates whether the most recent score was "bad" and the percent of previous scores for that restaurant that were "bad".

`explore.r` fits a logistic regression model to the data, using percent of previous scores that were "bad" as a predictor, and controlling for city. The results from R are below:

	Call:
	glm(formula = bad_now ~ pct_bad_previous + as.factor(inspection_authority), 
		family = "binomial", data = data)

	Deviance Residuals: 
		Min       1Q   Median       3Q      Max  
	-1.7715  -0.9239  -0.6911   1.1564   1.7602  

	Coefficients:
											Estimate Std. Error z value Pr(>|z|)    
	(Intercept)                             -0.02449    0.02442  -1.003    0.316    
	pct_bad_previous                         1.36009    0.03562  38.186   <2e-16 ***
	as.factor(inspection_authority)New York -1.28597    0.02656 -48.425   <2e-16 ***
	---
	Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

	(Dispersion parameter for binomial family taken to be 1)

		Null deviance: 40476  on 29777  degrees of freedom
	Residual deviance: 36608  on 29775  degrees of freedom
	AIC: 36614

	Number of Fisher Scoring iterations: 4

These results show a strong, statistically significant relationship between percentage of previous scores for a restaurant that were "bad" and their current score being "bad". In fact, `exp(1.36) = 3.9`, so the odds of restaurants that had 100% "bad" scores on previous inspections getting a "bad" score on their most recent inspection were nearly 4x higher than the odds for restaurants that had 0% "bad" scores on previous inspections. (For clarity, `pct_bad_previous` ranged from 0 to 1, not 0 to 100.) These results are not surprising at all. It was a fairly obvious hypothesis.

There's a lot of additional detail that gets glossed over here, such as New York's practice of going back and re-inspecting before assigning scores. An interaction term between city and `pct_bad_previous` is probably warranted. Again, all this was skipped in the interest of time.

## Building an API

I spent some time exploring an API for rating the likelihood of a restaurant failing an inspection. All cities in the data set had a concept of violation codes and various outcomes, so I decided to see if I could predict outcomes based on unique violation codes. Since violation codes were different for each city, I focused on Chicago. With more time you could pool data by constructing a data model that mapped codes to common categories, or you could use Natural Language Processing to read their descriptions. However, with this data, I'm not sure that would be the most useful approach. Rather, I think it might be most helpful to have a single model that could be easily retrained for each city's data. Same model structure, but input codes and output results might be slightly different, depending on local laws. You'd have to see how things evolved as you got more than 2 cities. At any rate, I started with Chicago, but the code could have easily been extended to automatically train the same model for both cities and deploy both to the API. Again, time constraints.

In `train.py`, I trained a Support Vector Classifier to look at the violation codes assigned to a restaurant during an inspection and predict whether the restaurant would pass, pass with conditions, or fail. It initially achieved 70% accuracy, largely by predicting "pass" all of the time. So, I re-weighted the classes to punish the model for missing a "fail" or "pass with conditions." While this reduced overall accuracy, it made the model much more conservative in grading inspections, and more likely to catch ones that were likely to be bad. Here's the resulting confusion matrix (in row percentages) when the model was applied to a portion of the data reserved for testing:

![confusion matrix](https://i.imgur.com/ZhACmBP.png)

It's not a spectacular model, but for each true category, it does get things right at least the majority of the time. It's learned *something*, anyway.

With more time, it could certainly be better. Chicago has several different violation types that nest within each code, and they're delineated by the violation description. Using violation descriptions to predict outcomes increased model accuracy to over 90%. However, I stuck with codes for now for the simplicity of accessing the API.

In `api.py`, you'll find a simple flask-based JSON/REST API that actually deploys the model. Running it in test mode on my local machine shows it up and running!

For example, suppose a restaurant got cited for violation codes 3, 7, 2, and 9. You'd access the API like so:

	curl -d "{\"violations\":[\"3\", \"7\", \"2\", \"9\"]}" -H "Content-Type: application/json" -X POST http://localhost:5000/score

And you'd get back the following:

    {"Fail_probability":0.41559334432788936,"Pass w/ Conditions_probability":0.35941149771475617,"Pass_probability":0.22499515795735467,"prediction":"Fail"}

This tells us that the restaurant would most likely fail this inspection, that it would have a roughly 42% chance of failing, and only a 22% chance of passing. Not bad!