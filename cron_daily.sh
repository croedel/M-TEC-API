#/bin/bash

PATH=$PATH:/usr/bin
BASE_DIR="/home/pi/infotainment/MTEC_energybutler_API"
BASE_DATA_DIR="$BASE_DIR/data"

echo "`date '+%Y-%m-%d %H:%M:%S'` Data export started" 

# define pathname of data file + create dir, if not existing 
DATA_DIR="$BASE_DATA_DIR/`date -d yesterday +%Y`"
if [ ! -d "$DATA_DIR" ]
then
   mkdir -p $DATA_DIR
fi

# Export data for the whole month until "yesterday"
START_DATE="`date -d yesterday +%Y-%m-01`"
END_DATE="`date -d yesterday +%Y-%m-%d`"
FNAME_MONTH="$DATA_DIR/`date -d yesterday +%Y-%m`_month.csv"
python3 $BASE_DIR/export_data.py -t month -s $START_DATE -e $END_DATE -d , -f $FNAME_MONTH 
FNAME_DAY="$DATA_DIR/`date -d yesterday +%Y-%m`_day.csv"
python3 $BASE_DIR/export_data.py -t day -s $START_DATE -e $END_DATE -d , -f $FNAME_DAY

# concatenate all month files to a year file
FNAME_YEAR="$BASE_DATA_DIR/`date -d yesterday +%Y`_year.csv"
head -1 $FNAME_MONTH > $FNAME_YEAR 
for f in $DATA_DIR/*_month.csv
do
   tail -n +2 $f >> $FNAME_YEAR 
done

# concatenate all year files to a lifetime file
FNAME_LIFETIME="$BASE_DATA_DIR/lifetime.csv"
head -1 $FNAME_MONTH > $FNAME_LIFETIME 
for f in $BASE_DATA_DIR/*_year.csv
do
   tail -n +2 $f >> $FNAME_LIFETIME 
done

echo "`date '+%Y-%m-%d %H:%M:%S'` Data export completed" 
