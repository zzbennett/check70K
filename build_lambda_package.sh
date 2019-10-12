rm -rf ./package
rm -f ./check70kPackage.zip
pip install -r requirements.txt -t ./package
chmod -R 755 ./package
cp *.py *.json ./package
zip -r ./check70kPackage.zip ./package

echo "Package was built. Upload ./check70kPackage.zip to lambda manually"