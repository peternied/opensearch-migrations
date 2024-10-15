VPC_ID=vpc-09c3353b7bc4ca759


lookupVpiInfo() {
    echo "Collecting subnet IDs and availability zones..."
    SUBNETS_JSON=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].[SubnetId,AvailabilityZone]' --output json)

    if [ $? -ne 0 ]; then
    echo "Error retrieving subnet information. Please check the VPC ID."
    exit 1
    fi

    SUBNET_IDS=$(echo $SUBNETS_JSON | jq -r '.[].[0]' | paste -sd "," -)
    AVAILABILITY_ZONES=$(echo $SUBNETS_JSON | jq -r '.[].[1]' | paste -sd "," -)

    echo "Collecting route table IDs for subnets..."
    ROUTE_TABLE_IDS=""
    for SUBNET_ID in $(echo $SUBNET_IDS | tr ',' ' '); do
    ROUTE_TABLE_ID=$(aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=$SUBNET_ID" --query 'RouteTables[0].RouteTableId' --output text)
    if [ "$ROUTE_TABLE_ID" == "None" ]; then
        echo "No route table found for subnet $SUBNET_ID."
        exit 1
    fi
    ROUTE_TABLE_IDS="${ROUTE_TABLE_IDS}${ROUTE_TABLE_ID},"
    done
    # Remove trailing comma
    ROUTE_TABLE_IDS=${ROUTE_TABLE_IDS%,}

    echo "---"
    echo "VpcId=$VPC_ID"
    echo "PrivateSubnetIds=$SUBNET_IDS"
    echo "AvailabilityZones=$AVAILABILITY_ZONES"
    echo "PrivateSubnetRouteTableIds=$ROUTE_TABLE_IDS"
}
lookupVpiInfo