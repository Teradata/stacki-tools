cat << "HEREDOC"


      ____  _             _    _ 
     / ___|| |_ __ _  ___| | _(_)
     \___ \| __/ _` |/ __| |/ / |
      ___) | || (_| | (__|   <| |
     |____/ \__\__,_|\___|_|\_\_|
          ____   ___   ____      
         | __ ) / _ \ | __ )     
         |  _ \| | | ||  _ \     
         | |_) | |_| || |_) |    
         |____(_)___(_)____(_)


         Bot-Operated Builds


HEREDOC

if [ ! -d /export/nightly/stacki/ ]; then
	return
fi

LATEST_ISO=`ls -t /export/nightly/stacki/stacki-[0-9]*.iso 2>/dev/null | head -1`
ISO_COMMIT=`basename $LATEST_ISO 2>/dev/null | sed -rn "s/stacki-\w+.\w*_(\w+)-.*.iso/\1/p"` 
cd /export/build/stacki/
COMMIT_MSG=`git log -n 1 --pretty=short $ISO_COMMIT`
if [ "COMMIT_MSG" == "" ]; then
	git pull >/dev/null 2>&1
	COMMIT_MSG=`git log -n 1 --pretty=short $ISO_COMMIT`
fi

if [ "$LATEST_ISO" != "" ]; then
	echo "Latest nightly build:"
	echo "	$LATEST_ISO (`date -r $LATEST_ISO`)"
	echo
	echo "For your convenience:"
	echo "	scp `hostname`:${LATEST_ISO} ."
	echo
	echo "Checksums:"
	grep --color=never `basename $LATEST_ISO` /export/nightly/checksums.txt
	echo
	echo "Based on:"
	echo "$COMMIT_MSG"
	echo
fi

pallets=()
echo "Stacki build server has scheduled builds for:"
for pallet in `crontab -l | grep do_build.yml | tr '/.' ' ' | rev | cut --delimiter=' ' --fields=2 | rev `; do
	pallets+=($pallet)
done

for pallet in `crontab -l | grep build_.*yml -o | sed -n -r 's/build_(.*)\.yml/\1/p' `; do
	pallets+=($pallet)
done

pallets=($(for pallet in ${pallets[@]}; do echo $pallet; done | sort))
printf ' • %s\n' "${pallets[@]}"

echo
cd ~
