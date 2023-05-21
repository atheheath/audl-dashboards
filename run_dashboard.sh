export $(cat .env | xargs) && pushd src/ && python app.py
popd
