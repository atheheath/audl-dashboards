export $(cat .env | xargs) && pushd . && python app.py
popd
