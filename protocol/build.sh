# Make sure, protoc is installed; Ob Ubuntu:
# sudo apt install -y protobuf-compiler

pip install -qq mypy-protobuf
mkdir -p ./build
protoc --python_out=./build --mypy_out=./build ./src/TiraClientWebMessages.proto
echo "I compiled the proto files. You can find them in ./build/. Please copy them over to tira_app.proto."