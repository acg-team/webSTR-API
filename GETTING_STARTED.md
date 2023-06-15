# Webstr API Getting Started GUIDE

## How to access the WebSTR-API?  
WebSTR-API provides access to the data via different “endpoints” - addresses on the url that are formed in a certain way.
To access endpoints you can either use the [curl tool](https://curl.se/) in the Terminal or simply edit these the following links directly in your Browser. 
It is also possible to use WebSTR-API in your code, see Python and R examples at the bottom of this page.

## WebSTR-API output 
Default output is in JSON format, details for each endpoint are described in the documentation - [http://webstr-api.ucsd.edu/docs](http://webstr-api.ucsd.edu/docs)
It is also possible to download results in a csv format by adding "&download=True" to each request. 
For example: [https://webstr-api.ucsd.edu/repeats?gene_names=HTT&download=True](https://webstr-api.ucsd.edu/repeats?gene_names=HTT&download=True) will download a
csv will all repeats associated with the HTT gene in repeats.scv file. 

## Most common queries to WebSTR-API

### Getting repeats

If you are interested in extracting STRs located in the genomic region of your interest, “repeats” endpoint would be the most important.
It is possible to access genomic region of interest via genomic coordinates, common gene names or Ensemble IDs.

Access repeats via genomic coordinates: 

Example request for chromosome 4, coordinates 3186810-4121716:

[http://webstr-api.ucsd.edu/repeats?region_query=4:3186810-4121716](http://webstr-api.ucsd.edu/repeats?region_query=4:3186810-4121716)

Example output:
```
[{"repeat_id":86397,"chr":"chr4","start":3186839,"end":3186860,"msa":"T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T,T",
"motif":"T","period":1,"copies":22,"ensembl_id":"ENSG00000197386","strand":"+","gene_name":"HTT",
"gene_desc":"huntingtin","total_calls":29,"frac_variable":0.896551724137931,"avg_size_diff":3.68965517241379},
{"repeat_id":1550762,"chr":"chr4","start":3313970,"end":3313989,"msa":null,"motif":"AAAT",
"period":4,"copies":5,"ensembl_id":"ENSG00000248840","strand":"+","gene_name":null,"gene_desc":null,
"total_calls":null,"frac_variable":null,"avg_size_diff":null},
....
]
```

Access repeats via common gene names: 
[http://webstr-api.ucsd.edu/repeats?gene_names=HTT](http://webstr-api.ucsd.edu/repeats?gene_names=HTT)

Access repeats via EnsembleID:
[http://webstr-api.ucsd.edu/repeats?ensembl_ids=ENSG00000197386](http://webstr-api.ucsd.edu/repeats?ensembl_ids=ENSG00000197386)

To get repeats from several genes, chain gene_names parameters together in the following manner:
 [https://webstr-api.ucsd.edu/repeats/?gene_names=HTT&gene_names=AGRN](http://webstr-api.ucsd.edu/repeats?gene_names=HTT&gene_names=AGRN)


### Getting extended information for a repeat of interest

You will need a repeat id number from our database, available via repeats endpoint, see example above. 
Example request:
 http://webstr-api.ucsd.edu/repeatinfo/?repeat_id=1


### Getting extended information for a gene of interest:

Via gene name
gene features: http://webstr-api.ucsd.edu/genefeatures/?gene_names=HTT
