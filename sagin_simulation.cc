#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/mobility-module.h"
#include "ns3/applications-module.h"
#include "ns3/netanim-module.h"
#include "ns3/flow-monitor-module.h"

// Add these headers for threading and socket communication
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <string>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("SaginSimulation");

// Global maps to store NetDevices and Channels
std::map<std::pair<uint32_t, uint32_t>, Ptr<PointToPointNetDevice>> netDeviceMap;
std::map<std::pair<uint32_t, uint32_t>, Ptr<PointToPointChannel>> channelMap;

// Control server function to receive commands
void ControlServer(std::queue<std::string> &commandQueue, std::mutex &queueMutex, std::condition_variable &cv)
{
    int sockfd;
    struct sockaddr_in servaddr;

    // Create UDP socket
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);

    // Zero out the server address structure
    memset(&servaddr, 0, sizeof(servaddr));

    // Set up the server address
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY); // Listen on all interfaces
    servaddr.sin_port = htons(5555);              // Port number

    // Bind the socket
    bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr));

    char buffer[1024];

    while (true)
    {
        int n = recvfrom(sockfd, buffer, 1024, 0, NULL, NULL);
        buffer[n] = '\0';
        std::string command(buffer);

        // Add the command to the queue
        {
            std::lock_guard<std::mutex> lock(queueMutex);
            commandQueue.push(command);
        }
        cv.notify_one();
    }
}

// Function to increase bandwidth
void IncreaseBandwidth()
{
    auto key = std::make_pair(0, 0); // Adjust indices as needed
    if (netDeviceMap.find(key) != netDeviceMap.end())
    {
        Ptr<PointToPointNetDevice> device = netDeviceMap[key];
        device->SetDataRate(DataRate("2Gbps"));

        NS_LOG_UNCOND("Bandwidth increased between Ground Node 0 and Satellite Node 0");
    }
    else
    {
        NS_LOG_ERROR("NetDevice not found for the specified nodes.");
    }
}

// Function to decrease latency
void DecreaseLatency()
{
    auto key = std::make_pair(0, 0); // Adjust indices as needed
    if (channelMap.find(key) != channelMap.end())
    {
        Ptr<PointToPointChannel> channel = channelMap[key];
        channel->SetAttribute("Delay", TimeValue(MilliSeconds(10)));

        NS_LOG_UNCOND("Latency decreased between Ground Node 0 and Satellite Node 0");
    }
    else
    {
        NS_LOG_ERROR("Channel not found for the specified nodes.");
    }
}

// Function to execute received commands
void ExecuteCommand(const std::string &command)
{
    if (command == "increase_bandwidth")
    {
        Simulator::ScheduleNow(&IncreaseBandwidth);
    }
    else if (command == "decrease_latency")
    {
        Simulator::ScheduleNow(&DecreaseLatency);
    }
    else
    {
        NS_LOG_WARN("Unknown command received: " << command);
    }
}

// Command processing function
void ProcessCommands(std::queue<std::string> &commandQueue, std::mutex &queueMutex, std::condition_variable &cv)
{
    while (true)
    {
        std::unique_lock<std::mutex> lock(queueMutex);
        cv.wait(lock, [&] { return !commandQueue.empty(); });

        while (!commandQueue.empty())
        {
            std::string command = commandQueue.front();
            commandQueue.pop();
            lock.unlock();

            ExecuteCommand(command);

            lock.lock();
        }
    }
}

int main(int argc, char *argv[])
{
    double simTime = 100.0; // seconds

    CommandLine cmd;
    cmd.Parse(argc, argv);

    // Logging start
    NS_LOG_UNCOND("Starting SAGIN simulation...");

    // Create nodes
    NodeContainer satelliteNodes;
    satelliteNodes.Create(3);

    NodeContainer groundNodes;
    groundNodes.Create(3);

    NodeContainer allNodes;
    allNodes.Add(satelliteNodes);
    allNodes.Add(groundNodes);

    NS_LOG_UNCOND("Number of satellite nodes: " << satelliteNodes.GetN());
    NS_LOG_UNCOND("Number of ground nodes: " << groundNodes.GetN());

    // Install internet stack
    InternetStackHelper internet;
    internet.Install(allNodes);

    // Set up mobility
    MobilityHelper satelliteMobility;
    satelliteMobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    Ptr<ListPositionAllocator> satellitePositionAlloc = CreateObject<ListPositionAllocator>();
    satellitePositionAlloc->Add(Vector(1000.0, 0.0, 0.0));   // Satellite 1
    satellitePositionAlloc->Add(Vector(0.0, 1000.0, 0.0));   // Satellite 2
    satellitePositionAlloc->Add(Vector(-1000.0, 0.0, 0.0));  // Satellite 3
    satelliteMobility.SetPositionAllocator(satellitePositionAlloc);
    satelliteMobility.Install(satelliteNodes);

    MobilityHelper groundMobility;
    groundMobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    Ptr<ListPositionAllocator> groundPositionAlloc = CreateObject<ListPositionAllocator>();
    groundPositionAlloc->Add(Vector(500.0, 0.0, 0.0));   // Ground Node 1
    groundPositionAlloc->Add(Vector(0.0, 500.0, 0.0));   // Ground Node 2
    groundPositionAlloc->Add(Vector(-500.0, 0.0, 0.0));  // Ground Node 3
    groundMobility.SetPositionAllocator(groundPositionAlloc);
    groundMobility.Install(groundNodes);

    NS_LOG_UNCOND("Mobility models installed for all nodes.");

    // Create links
    NetDeviceContainer devices;
    Ipv4AddressHelper address;

    for (uint32_t i = 0; i < groundNodes.GetN(); ++i)
    {
        for (uint32_t j = 0; j < satelliteNodes.GetN(); ++j)
        {
            // Customize attributes
            std::string dataRate = "500Mbps";
            std::string delay = "50ms";

            if (i == 0 && j == 0)
            {
                dataRate = "1Gbps";
                delay = "20ms";
            }
            else if (i == 1 && j == 1)
            {
                dataRate = "800Mbps";
                delay = "30ms";
            }
            else if (i == 2 && j == 2)
            {
                dataRate = "600Mbps";
                delay = "40ms";
            }

            // Set up Point-to-Point link
            PointToPointHelper customP2p;
            customP2p.SetDeviceAttribute("DataRate", StringValue(dataRate));
            customP2p.SetChannelAttribute("Delay", StringValue(delay));

            NetDeviceContainer link = customP2p.Install(groundNodes.Get(i), satelliteNodes.Get(j));
            devices.Add(link);

            // Store NetDevices
            Ptr<PointToPointNetDevice> groundDevice = DynamicCast<PointToPointNetDevice>(link.Get(0));
            Ptr<PointToPointNetDevice> satelliteDevice = DynamicCast<PointToPointNetDevice>(link.Get(1));
            netDeviceMap[std::make_pair(i, j)] = groundDevice;

            // Store Channel
            Ptr<PointToPointChannel> channel = groundDevice->GetChannel()->GetObject<PointToPointChannel>();
            channelMap[std::make_pair(i, j)] = channel;

            // Assign IP addresses
            std::ostringstream subnet;
            subnet << "10." << i << "." << j << ".0";
            address.SetBase(subnet.str().c_str(), "255.255.255.0");
            address.Assign(link);

            NS_LOG_UNCOND("Link created between Ground Node " << i << " and Satellite Node " << j
                           << " with DataRate: " << dataRate << " and Delay: " << delay);
        }
    }

    // Install applications
    uint16_t echoPort = 9;

    UdpEchoServerHelper echoServer(echoPort);
    ApplicationContainer serverApps;
    for (uint32_t i = 0; i < groundNodes.GetN(); ++i)
    {
        serverApps.Add(echoServer.Install(groundNodes.Get(i)));
    }
    serverApps.Start(Seconds(1.0));
    serverApps.Stop(Seconds(simTime - 1));

    UdpEchoClientHelper echoClient(Ipv4Address::GetAny(), echoPort);
    echoClient.SetAttribute("MaxPackets", UintegerValue(1000));
    echoClient.SetAttribute("Interval", TimeValue(Seconds(0.1)));
    echoClient.SetAttribute("PacketSize", UintegerValue(1024));

    ApplicationContainer clientApps;

    for (uint32_t i = 0; i < satelliteNodes.GetN(); ++i)
    {
        for (uint32_t j = 0; j < groundNodes.GetN(); ++j)
        {
            Ptr<Node> groundNode = groundNodes.Get(j);
            Ptr<Ipv4> ipv4 = groundNode->GetObject<Ipv4>();

            if (!ipv4)
            {
                NS_LOG_ERROR("Ground Node " << j << " does not have an IPv4 interface!");
                continue;
            }

            uint32_t interfaceIndex = i * groundNodes.GetN() + j + 1;
            if (interfaceIndex >= ipv4->GetNInterfaces())
            {
                NS_LOG_ERROR("Invalid interface index for Ground Node " << j << ": " << interfaceIndex);
                continue;
            }

            Ipv4InterfaceAddress iaddr = ipv4->GetAddress(interfaceIndex, 0);
            Ipv4Address ipAddr = iaddr.GetLocal();

            if (ipAddr == Ipv4Address::GetAny())
            {
                NS_LOG_ERROR("Ground Node " << j << " has an invalid IP address at interface index: " << interfaceIndex);
                continue;
            }

            echoClient.SetAttribute("RemoteAddress", AddressValue(ipAddr));
            clientApps.Add(echoClient.Install(satelliteNodes.Get(i)));

            NS_LOG_UNCOND("Client installed on Satellite Node " << i << " targeting Ground Node " << j
                           << " with IP: " << ipAddr);
        }
    }

    clientApps.Start(Seconds(2.0));
    clientApps.Stop(Seconds(simTime - 1));

    // Enable tracing
    AsciiTraceHelper ascii;
    Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream("sagin_simulation.tr");
    internet.EnableAsciiIpv4All(stream);

    // Flow monitor for performance metrics
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    // Animation
    AnimationInterface anim("sagin_simulation.xml");

    
    // Register and assign custom icons for nodes
    uint32_t satelliteIcon = anim.AddResource("/Users/sajidalam/Documents/Procactive_LLMBased_Project/Procactive_LLMBased_Project_Updated/ns3/ns-allinone-3.37/ns-3.37/satellite.png");
    uint32_t groundIcon = anim.AddResource("/Users/sajidalam/Documents/Procactive_LLMBased_Project/Procactive_LLMBased_Project_Updated/ns3/ns-allinone-3.37/ns-3.37/ground_station.png");

    anim.UpdateNodeImage(satelliteNodes.Get(0)->GetId(), satelliteIcon);
    anim.UpdateNodeImage(satelliteNodes.Get(1)->GetId(), satelliteIcon);
    anim.UpdateNodeImage(satelliteNodes.Get(2)->GetId(), satelliteIcon);
    anim.UpdateNodeImage(groundNodes.Get(0)->GetId(), groundIcon);
    anim.UpdateNodeImage(groundNodes.Get(1)->GetId(), groundIcon);
    anim.UpdateNodeImage(groundNodes.Get(2)->GetId(), groundIcon);

    // Adjust node sizes for larger icons
    anim.UpdateNodeSize(satelliteNodes.Get(0)->GetId(), 120, 120);
    anim.UpdateNodeSize(satelliteNodes.Get(1)->GetId(), 120, 120);
    anim.UpdateNodeSize(satelliteNodes.Get(2)->GetId(), 120, 120);
    anim.UpdateNodeSize(groundNodes.Get(0)->GetId(), 100, 100);
    anim.UpdateNodeSize(groundNodes.Get(1)->GetId(), 100, 100);
    anim.UpdateNodeSize(groundNodes.Get(2)->GetId(), 100, 100);

    anim.EnablePacketMetadata(true); // Enable packet tracing in animation
    anim.EnableIpv4RouteTracking("routing_table.xml", Seconds(1), Seconds(simTime), Seconds(1));

    // Start the control server and command processor threads
    std::queue<std::string> commandQueue;
    std::mutex queueMutex;
    std::condition_variable cv;

    std::thread controlThread(ControlServer, std::ref(commandQueue), std::ref(queueMutex), std::ref(cv));
    std::thread commandThread(ProcessCommands, std::ref(commandQueue), std::ref(queueMutex), std::ref(cv));

    Simulator::Stop(Seconds(simTime));
    Simulator::Run();

    // Print flow monitor statistics
    monitor->SerializeToXmlFile("flowmon-results.xml", true, true);

    // Cleanup
    controlThread.detach();
    commandThread.detach();

    Simulator::Destroy();

    NS_LOG_UNCOND("Simulation completed successfully.");

    return 0;
}
