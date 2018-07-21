# Author:Roseline Batcha
# GEOG 777 Project 1
# Spatial analysis with IDW to find out the relationship between water nitrates concemntrations and cancer occurrences
# Python version 2.7.10

# Import the system modules
import arcpy
from arcpy import env
from arcpy.sa import *

# Run IDW on the well.shp

# Set environment settings
env.workspace = "C:\MyUW\SummerProject1"
arcpy.env.overwriteOutput = True
arcpy.env.resamplingMethod = "BILINEAR"

# Set the local variables
inPointFeatures = "well_nitrate.shp"
zField = "nitr_ran"
cellSize = ""
power = 1.25
searchRadius = RadiusVariable(10, 150000)

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Execute IDW
outIDW = Idw(inPointFeatures, zField, cellSize, power, searchRadius)

# Save output 
outIDW.save("C:\MyUW\SummerProject1\idw1")

print "IDW Raster saved, beginning to aggregate Cancer incidences to block group levels...."

# Aggregate the interpolated nitrate locations with the census tract level
# Run Zonal Statistics as Table on the IDW raster

# Set local variables
inZoneData = "cancer_tracts.shp"
zoneField = "GEOID10"
inValueRaster = "idw1"
outTable = "zonalStatTbl01.dbf"

# Execute ZonalStatisticsAsTable
outZSaT = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, 
                                 outTable, "NODATA", "MEAN")

print "Success!, Aggregation complete and feature join processing..."

# Attribute join the Zonal Statistics table to the cancer_tracts table

try:
    # Set environment settings    
    env.qualifiedFieldNames = False
    
    # Set local variables    
    inFeatures = "cancer_tracts.dbf"
    layerName = "cancer_tracts"
    joinTable = "zonalStatTbl01.dbf"
    joinField = "GEOID10"
    expression = ""
    outFeature = "cancerCensus"
    isCommon = "KEEP_COMMON"
    
    # Create a feature layer from the vegtype featureclass
    arcpy.MakeFeatureLayer_management (inFeatures,  layerName)
    
    # Join the feature layer to a table
    arcpy.AddJoin_management(layerName, joinField, joinTable, joinField, isCommon)
    
    # Select desired features from veg_layer
    #arcpy.SelectLayerByAttribute_management(layerName, "NEW_SELECTION", expression)
    
    # Copy the layer to a new permanent feature class
    arcpy.CopyFeatures_management(layerName, outFeature)

    print "Success! Regression processing..."
    
except Exception, e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    print "Line %i" % tb.tb_lineno
    print e.message

#############################
# Run Regression on the new joined censusjoin shapefile

arcpy.env.overwriteOutput = True
 
workspace = "C:\MyUW\SummerProject1" 

try:
    # Set the current workspace (to avoid having to specify the full path to the feature classes each time)
    arcpy.env.workspace = workspace

   # Process: Geographically Weighted Regression... 
    gwr = arcpy.GeographicallyWeightedRegression_stats("cancerCensus.shp", "canrate", 
                        "MEAN",
                        "CancerGWR.shp", "ADAPTIVE", "BANDWIDTH PARAMETER")
    
except:
    # If an error occurred when running the tool, print out the error message.
    print(arcpy.GetMessages())
print "Bingo!, OLS analysis Complete & Image stored."

                        

