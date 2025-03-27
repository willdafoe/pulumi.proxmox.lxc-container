PROJECT_NAME = pulumi.proxmox.lxc
STACK_NAME = willdafoe/test

all: install lint preview

install:
	pip install -r requirements.txt

lint:
	flake8 .

preview:
	pulumi preview --stack $(STACK_NAME)

up:
	pulumi up --stack $(STACK_NAME) --yes

destroy:
	pulumi destroy --stack $(STACK_NAME) --yes

refresh:
	pulumi refresh --stack $(STACK_NAME) --yes

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +

