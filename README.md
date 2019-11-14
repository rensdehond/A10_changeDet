# A10_changeDet

plan:

 - for each of the bgt objects that indicates a portal
	 - ~~*to do*:  which bgt objecten?~~
	 - BGT: `bgt.overbruggingsdeel`
	 - Kerngis: vKunstwerk_FeaturesToJSON >> `lower("OBJECTTEKST" ) = 'viaduct'`
	 	- When does A10 go under and when does it go over
	 - test area: `117813.6,487266.1,117942.1,487370.7`
	 - test area wkt: `wkt = 'POLYGON((117813.6 487266.1,117813.6 487370.7,117942.1 487370.7,117942.1 487266.1,117813.6 487266.1))'`
 - filter cars out for visualization and cleaning of data before clustering
 	- *to do*: 2018 < data cleaning
	- ~~*to do*: 2019~~ < visualization/data cleaning
 - read the points from the ept-folder
 	 - where is viewer hosted? 
	 - available to whom?
	 - *to do*: create potree tiles
	 - *to do*: create cesium tiles
## method 1
	- cluster on Z
		 - Assumption: the two biggest clusters are the top and bottom of the portal	
	 - CLUSTERS FOUND
	 - onderste 10 % (ofzo) vinden, ruis eruit halen en vergelijken
	 - 
		 
## method 2
	- validate method for calculating doorrijhoogte
	- calculeate doorrijhoogte for x portals
	- compare over different years



## vragen:
- Hoe definieren we de doorrijhoogte?
- willen we de doorijhoogte of alleen het verschil?


 - compare two clusters statistically
 	 - specify
 - write std, mean, etc to ???
	- 
