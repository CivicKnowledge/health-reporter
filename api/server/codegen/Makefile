.PHONY: all clean 

default: api

SWAGGER_INPUT := ../swagger.yaml

TARGET_LANG := dynamic-html
TARGET_LANG := html

SWAGGER_JAR := ./swagger-codegen/modules/swagger-codegen-cli/target/swagger-codegen-cli.jar
SWAGGER_BIN := java -jar ${SWAGGER_JAR}
DOC_DIR := ../docs/

clean: 
	rm -rf ./server
	rm -rf ${DOC_DIR}

api: swagger | $(SWAGGER_JAR)
	mkdir -p ./server 
	${SWAGGER_BIN} generate -DsupportPython2=true -i ${SWAGGER_INPUT} -l python-flask -o server/ 
	
help: swagger | $(SWAGGER_JAR)
	
	${SWAGGER_BIN} config-help -l python-flask
	

docs: swagger | $(SWAGGER_JAR)
	mkdir -p ${DOC_DIR}
	${SWAGGER_BIN} generate -i ${SWAGGER_INPUT} -l dynamic-html -o ${DOC_DIR}

swagger:
	@if ! command -v ${SWAGGER_BIN} > /dev/null 2>&1; then echo "Swagger not installed, Visit https://github.com/swagger-api/swagger-codegen/blob/master/README.md  to get swagger-codegen"; exit 0; fi

# Build the swagger codegen package

$(SWAGGER_JAR): 
	git clone https://github.com/swagger-api/swagger-codegen.git && cd swagger-codegen && mvn clean package
	