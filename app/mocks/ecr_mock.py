import random
from datetime import datetime, timedelta


def describe_repositories():

    repos = []

    for i in range(6):

        repos.append({

            "repositoryName": f"service-{i}",
            "repositoryUri": f"fake.ecr/service-{i}",
            "repositoryArn": f"arn:aws:ecr:repo/service-{i}",
            "createdAt": datetime.now() - timedelta(days=random.randint(100,800)),

            "imageTagMutability": random.choice(["MUTABLE","IMMUTABLE"]),

            "imageScanningConfiguration":{
                "scanOnPush": random.choice([True,False])
            },

            "encryptionConfiguration":{
                "encryptionType": random.choice(["AES256","KMS"])
            }

        })

    return repos


def describe_images(repository_name):

    images = []

    for _ in range(random.randint(3,20)):

        images.append({

            "imageDigest": f"digest-{random.randint(1,9999)}",

            "imageSizeInBytes": random.randint(
                50_000_000,
                600_000_000
            ),

            "imagePushedAt":
                datetime.now() - timedelta(days=random.randint(1,200)),

            "imageTags":
                [f"v{random.randint(1,10)}"]

        })

    return images


def describe_image_scan_findings(repository_name, image_digest):

    return {

        "imageScanFindings":{

            "findingSeverityCounts":{

                "CRITICAL": random.randint(0,1),
                "HIGH": random.randint(0,3),
                "MEDIUM": random.randint(0,6),
                "LOW": random.randint(0,12)

            }

        }

    }


def get_lifecycle_policy(repository_name):

    if random.random() > 0.5:
        return {"policy": "exists"}

    return None


def get_repository_policy(repository_name):

    if random.random() > 0.5:
        return {"policy": "exists"}

    return None


def list_tags_for_resource(repository_arn):

    tags = []

    for i in range(random.randint(0,5)):

        tags.append({

            "Key": f"tag{i}",
            "Value": f"value{i}"

        })

    return tags