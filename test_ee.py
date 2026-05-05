import ee

ee.Initialize(project="earth-engine-project-495404")

print("✅ Earth Engine connected!")

number = ee.Number(10).add(5)
print(number.getInfo())