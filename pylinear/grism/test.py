from yaml import load,Loader


with open('instruments.yml') as stream:   # 'document.yaml' contains a single YAML document.
    x=load(stream)

print(x)
