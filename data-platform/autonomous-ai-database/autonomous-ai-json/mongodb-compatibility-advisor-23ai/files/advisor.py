import argparse
import sys

supported_keywords = ["$gt","$gte","$lt","$and","$not","$or","$nor","$ne","$eq","$in","$lte","$nin","$exists","$type","$regex","$text","$near","$nearSphere","$size","$natural","$inc","$min","$max",
                        "$rename","$set","$addToSet","$pop","$pull","$push","$pullAll","$each","$position","$sort","$bit","$count","$limit","$match","$skip","$slice","$mod","$geoIntersects",
                        "$geoWithin","$all","$elemMatch","$rand","$mul","$setOnInsert","$abs","$addFields","$bucket","$collStats","$facet","$group","$out","$project","$replaceRoot","$sortByCount",
                        "$unionWith","$unset","$unwind","$add","$arrayElemAt","$arrayToObject","$bottom","$ceil","$cmp","$concatArrays","$concat","$cond","$dateFromString","$dateToString","$divide",
                        "$exp","$filter","$first","$firstN","$floor","$ifNull","$isArray","$isNumber","$last","$let","$literal","$ln","$ltrim","$mergeObjects","$multiply","$objectToArray","$pow",
                        "$reverseArray","$round","$rtrim","$setUnion","$sortArray","$sqrt","$subtract","$top","$toString","$toLower","$toUpper","$trim","$trunc","$zip","$currentDate","$lastN","$reduce",
                        "$strcasecmp","$sql","$stdDevPop","$stdDevSamp","$replaceWith","$sample","$avg","$indexOfArray","$indexOfCP","$log","$log10","$sum","$switch","$toBool","$toDate","$toDouble"]  
 
not_supported_keywords=["$expr","$jsonSchema","$box","$center","$centerSphere","$maxDistance","$minDistance","$polygon","$bitsAllClear","$bitsAllSet","$bitsANyClear","$bitsAnySet","$currentData",
                        "$accumulator","$acos","$acosh","$bucketAuto","$changeStream","$currentOp","$densify","$documents","$fill","$geoNear","$graphLookup","$indexStats","$lookup","$merge","$redact",
                        "$search","$searchMeta","$setWindowFields","$allElementsTrue","$anyElementTrue","$asin","$asinh","$atan","$atan2","$atanh","$binarySize","$bottomN",
                        "$bsonSize","$convert","$cosh","$cosh","$covariancePop","$covarianceSamp","$dateAdd","$dateDiff","$dateFromParts","$datesubtract","$dateToParts","$dateTrunc","$dayOfMonth","$dayOfWeek",
                        "$dayOfYear","$degreesToRadians","$denseRank","$derivative","$documentNumber","$expMovingAvg","$function","$getField","$hour","$indexOfBytes","$integral",
                        "$isoDayOfWeek","$isoWeek","$isoWeekYear","$linearFill","$map","$maxN","$meta","$minN","$millisecond","$minute","$month","$radiansToDegrees","$range","$rank","$regexFind",
                        "$regexFindAll","$regexMatch","$replaceOne","$replaceAll","$sampleRate","$second","$setDifference","$setEquals","$setField","$setIntersection","$setIsSubset","$shift","$sin","$sinh",
                        "$split","$stsDevPop","$stsDevSamp","$strLenBytes","$strLenCP","$substr","$substrCP","$tan","$tanh","$toDecimal","$toInt","$toLong",
                        "$toObjectId","$topN","$tsIncrement","$tsSecond","$unsetField","$week","$year"]

operations=["\"command\":{\"find\"","\"command\":{\"update\"","\"command\":{\"insert\"","\"command\":{\"delete\"","\"command\":{\"aggregate\"","\"command\":{\"mapReduce\"","\"command\":{\"getMore\"","\"command\":{\"findAndModify\""]

def main(argv):
    parser=argparse.ArgumentParser()
    parser.add_argument("--file",dest="file",help="Set the MongoDB log file to analyze")

    argv = parser.parse_args()

    if argv.file is None:
        parser.error("--file is required")

    mongo_log = read_log(argv.file)
    supported_dictionary,not_supported_dictionary,operation_dictionary = search(mongo_log)
    generate_report(supported_dictionary,not_supported_dictionary,operation_dictionary)


def read_log(file):
    with open(file, 'r') as f:
        text = f.readlines()
        return text


def search(input_file):

    supported_dictionary = dict()
    not_supported_dictionary = dict()
    operation_dictionary=dict()

    for line in input_file:
        for keyword in supported_keywords:
            if keyword in line:
                if not keyword in supported_dictionary:
                   supported_dictionary[keyword]=1
                else:
                   supported_dictionary[keyword]+=1

        for keyword in not_supported_keywords:
            if keyword in line:
                if not keyword in not_supported_dictionary:
                   not_supported_dictionary[keyword]=1
                else:
                   not_supported_dictionary[keyword]+=1

        for keyword in operations:
            if keyword in line:
                if not keyword in operation_dictionary:
                   operation_dictionary[keyword]=1
                else:
                   operation_dictionary[keyword]+=1


    return supported_dictionary,not_supported_dictionary,operation_dictionary




def generate_report(supported_dictionary,not_supported_dictionary,operations_dictionary):

    #Calculate aggregation pipelines perc
    total= sum(supported_dictionary.values()) + sum(not_supported_dictionary.values())
    total_supported=sum(supported_dictionary.values())
    total_not_supported=sum(not_supported_dictionary.values())
    if total==0:
        perc=0
    else:
        perc=round(total_supported/total*100)

    #Calculate operations perc
    total_operations=sum(operations_dictionary.values()) 

    supp_find=operations_dictionary["\"command\":{\"find\""] if "\"command\":{\"find\"" in operations_dictionary else 0
    supp_delete=operations_dictionary["\"command\":{\"delete\""] if "\"command\":{\"delete\"" in operations_dictionary else 0
    supp_insert=operations_dictionary["\"command\":{\"insert\""] if "\"command\":{\"insert\"" in operations_dictionary else 0
    supp_update=operations_dictionary["\"command\":{\"update\""] if "\"command\":{\"update\"" in operations_dictionary else 0
    supp_findAndModify=operations_dictionary["\"command\":{\"findAndModify\""] if "\"command\":{\"findAndModify\"" in operations_dictionary else 0
    supp_getMore=operations_dictionary["\"command\":{\"getMore\""] if "\"command\":{\"getMore\"" in operations_dictionary else 0

    supported_operations=supp_find + supp_delete + supp_insert + supp_update + supp_findAndModify + supp_getMore
    
    
    if total_operations==0:
        perc_operations=0
    else:
        perc_operations=round(supported_operations/total_operations*100)

    #Calculate overall compatibility per

    if(perc_operations)==0:
        overall_supported=0
    else:
        overall_supported=(perc + perc_operations)/2


    with open('report_advisor.txt','w') as f: 
        f.write("Report Summary for 23ai: " +"\n")
        f.write("*****************************" +"\n\n\n")
        


        f.write("Summary of aggregation operators found: your operators are " + str(perc)+"% compatible with MongoDB API \n" )
        f.write("****************************************************************************************************" +"\n")

        f.write(" - Total Aggregation Pipelines found: " + str(total)+"\n")
        f.write(" - Total Supported Aggregation Pipelines: " + str(total_supported)+"\n")
        f.write(" - Total Not Supported Aggregation Pipelines: " + str(total_not_supported)+"\n\n\n")
        


        f.write("List of supported aggregation operators and the number of times it appears: \n")
        f.write("********************************************************************************" +"\n")
        f.write(str(supported_dictionary)+"\n\n\n")
        

        f.write("List of NOT supported aggregation operators and the number of times it appears: \n" )
        f.write("********************************************************************************" +"\n")
        
        f.write(str(not_supported_dictionary)+"\n\n\n")

        f.write("Summary of operations found: your operations are " + str(perc_operations)+"% compatible with MongoDB API \n" )
        f.write("*************************************************************************************" +"\n")

        
        if '\"command\":{\"find\"' in operations_dictionary: 
            f.write(" - Query operations using find: "+str(operations_dictionary["\"command\":{\"find\""])+"\n")

        if '\"command\":{\"delete\"' in operations_dictionary:    
            f.write(" - Delete operations : "+str(operations_dictionary["\"command\":{\"delete\""])+"\n")


        if '\"command\":{\"insert\"' in operations_dictionary: 
            f.write(" - Insert operations : "+str(operations_dictionary["\"command\":{\"insert\""])+"\n")
        
        if '\"command\":{\"update\"' in operations_dictionary:
            f.write(" - Update operations : "+str(operations_dictionary["\"command\":{\"update\""])+"\n")

        if '\"command\":{\"findAndModify\"' in operations_dictionary:
            f.write(" - findAndModify operations : "+str(operations_dictionary["\"command\":{\"findAndModify\""])+"\n")
        
        if '\"command\":{\"getMore\"' in operations_dictionary:
            f.write(" - getMore operations : "+str(operations_dictionary["\"command\":{\"getMore\""])+"\n")
        
        if "\"command\":{\"aggregate\"" in operations_dictionary:
            f.write(" - Aggregate operations** : "+str(operations_dictionary["\"command\":{\"aggregate\""])+"\n")
        
        if "\"command\":{\"mapReduce\"" in operations_dictionary:
            f.write(" - mapReduce operations** : "+str(operations_dictionary["\"command\":{\"mapReduce\""])+"\n"+"\n"+"\n"+"\n")

        f.write("\n"+"\n"+ " ** Operations not supported.\n")
        f.write(" Insert and updates could not be accurate number as appears more in the log."+"\n"+"\n"+"\n"+"\n")


if __name__ == "__main__":
    main(sys.argv[1:])