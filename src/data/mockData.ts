import type { Post } from '../types';

export const mockPosts: Post[] = [
  {
    id: '1',
    userHandle: '@mumbai_citizen',
    platform: 'twitter',
    content: 'URGENT: Heavy flooding in Andheri East! Water level reached knee-deep on main road. Traffic completely stopped. People abandoning vehicles. Need immediate assistance! � #MumbaiFloods #Emergency',
    imageUrl: 'https://via.placeholder.com/400x300/3b82f6/ffffff?text=Mumbai+Flooding',
    tags: ['#MumbaiFloods', '#Emergency', '#AndheriEast', '#Help'],
    location: {
      lat: 19.1197,
      lng: 72.8697,
      name: 'Andheri East, Mumbai'
    },
    timestamp: new Date('2025-08-23T02:30:00Z'),
    upvotes: 324,
    downvotes: 2
  },
  {
    id: '2',
    userHandle: '@chennai_alert',
    platform: 'reddit',
    content: 'Cyclone warning update: Very severe cyclonic storm approaching Chennai coast. Winds already reaching 80 kmph in coastal areas. Please evacuate low-lying areas immediately. Stay safe! #CycloneAlert #Chennai',
    tags: ['#CycloneAlert', '#Chennai', '#Evacuation', '#StormWatch'],
    location: {
      lat: 13.0827,
      lng: 80.2707,
      name: 'Marina Beach, Chennai'
    },
    timestamp: new Date('2025-08-23T01:45:00Z'),
    upvotes: 567,
    downvotes: 5
  },
  {
    id: '3',
    userHandle: '@delhi_smoke',
    platform: 'instagram',
    content: 'Massive fire broke out in Karol Bagh market! Thick black smoke visible from kilometers away. Fire brigade on spot but flames spreading rapidly. Shops evacuated. Pray for everyone\'s safety 🔥 #DelhiFire #KarolBagh',
    imageUrl: 'https://via.placeholder.com/400x300/ef4444/ffffff?text=Delhi+Fire',
    tags: ['#DelhiFire', '#KarolBagh', '#Emergency', '#FireBrigade'],
    location: {
      lat: 28.6519,
      lng: 77.1909,
      name: 'Karol Bagh, New Delhi'
    },
    timestamp: new Date('2025-08-23T01:15:00Z'),
    upvotes: 892,
    downvotes: 12
  },
  {
    id: '4',
    userHandle: '@bengaluru_resident',
    platform: 'twitter',
    content: 'LANDSLIDE WARNING: Heavy rains causing soil erosion near Electronic City. Multiple roads blocked, houses at risk. Residents being evacuated. Avoid the area completely! #BangaloreLandslide #SafetyAlert',
    tags: ['#BangaloreLandslide', '#SafetyAlert', '#ElectronicCity', '#Evacuation'],
    location: {
      lat: 12.8456,
      lng: 77.6603,
      name: 'Electronic City, Bangalore'
    },
    timestamp: new Date('2025-08-23T00:50:00Z'),
    upvotes: 445,
    downvotes: 8
  },
  {
    id: '5',
    userHandle: '@pune_emergency',
    platform: 'facebook',
    content: 'Breaking: Major earthquake felt in Pune! Buildings swaying, people rushing out. Magnitude felt around 5.2. No major damage reported yet but aftershocks expected. Stay in open areas! #PuneEarthquake #SafetyFirst',
    imageUrl: 'https://via.placeholder.com/400x300/8b5cf6/ffffff?text=Earthquake+Alert',
    tags: ['#PuneEarthquake', '#SafetyFirst', '#Aftershocks', '#Emergency'],
    location: {
      lat: 18.5204,
      lng: 73.8567,
      name: 'Pune City, Maharashtra'
    },
    timestamp: new Date('2025-08-23T00:20:00Z'),
    upvotes: 1203,
    downvotes: 15
  },
  {
    id: '6',
    userHandle: '@kolkata_witness',
    platform: 'twitter',
    content: 'BREAKING: Bridge collapse on Howrah! People trapped underneath, rescue operations underway. Avoid the area, ambulances rushing to scene. This is devastating! Prayers needed 🙏 #KolkataBridge #Emergency',
    tags: ['#KolkataBridge', '#Emergency', '#Howrah', '#RescueOperation'],
    location: {
      lat: 22.5726,
      lng: 88.3639,
      name: 'Howrah Bridge, Kolkata'
    },
    timestamp: new Date('2025-08-22T23:45:00Z'),
    upvotes: 1567,
    downvotes: 23
  },
  {
    id: '7',
    userHandle: '@hyderabad_floods',
    platform: 'reddit',
    content: 'FLASH FLOOD ALERT: Sudden water surge in Hussain Sagar area due to dam overflow. Low-lying areas getting submerged rapidly. Immediate evacuation needed for lakeside colonies! #HyderabadFloods #DamOverflow',
    tags: ['#HyderabadFloods', '#DamOverflow', '#HussainSagar', '#FlashFlood'],
    location: {
      lat: 17.4239,
      lng: 78.4738,
      name: 'Hussain Sagar, Hyderabad'
    },
    timestamp: new Date('2025-08-22T23:20:00Z'),
    upvotes: 892,
    downvotes: 11
  },
  {
    id: '8',
    userHandle: '@kerala_floods',
    platform: 'instagram',
    content: 'Devastating scenes in Wayanad! Landslides blocking highways, villages cut off completely. Rescue helicopters trying to reach stranded families. Nature\'s fury is unimaginable 😢 #KeralaFloods #Wayanad',
    imageUrl: 'https://via.placeholder.com/400x300/059669/ffffff?text=Kerala+Landslide',
    tags: ['#KeralaFloods', '#Wayanad', '#Landslide', '#RescueOperation'],
    location: {
      lat: 11.6854,
      lng: 76.1320,
      name: 'Wayanad, Kerala'
    },
    timestamp: new Date('2025-08-22T22:55:00Z'),
    upvotes: 2103,
    downvotes: 18
  },
  {
    id: '9',
    userHandle: '@gujarat_emergency',
    platform: 'reddit',
    content: 'INDUSTRIAL ACCIDENT: Chemical plant explosion in GIDC Ankleshwar! Toxic gas leak reported, evacuation radius of 5km declared. Avoid the area, wear masks if nearby. Emergency services on site. #GujaratEmergency #ChemicalLeak',
    tags: ['#GujaratEmergency', '#ChemicalLeak', '#Ankleshwar', '#ToxicGas'],
    location: {
      lat: 21.6270,
      lng: 73.0151,
      name: 'Ankleshwar, Gujarat'
    },
    timestamp: new Date('2025-08-22T22:30:00Z'),
    upvotes: 1423,
    downvotes: 34
  },
  {
    id: '10',
    userHandle: '@rajasthan_heat',
    platform: 'twitter',
    content: 'EXTREME HEAT WAVE: Temperature crossed 48°C in Jodhpur! Multiple heat stroke cases reported in hospitals. Please stay indoors, drink plenty of water. This is dangerous! #RajasthanHeat #HeatWave #StayIndoors',
    imageUrl: 'https://via.placeholder.com/400x300/dc2626/ffffff?text=Heat+Wave+Alert',
    tags: ['#RajasthanHeat', '#HeatWave', '#StayIndoors', '#HealthAlert'],
    location: {
      lat: 26.2389,
      lng: 73.0243,
      name: 'Jodhpur, Rajasthan'
    },
    timestamp: new Date('2025-08-22T22:00:00Z'),
    upvotes: 756,
    downvotes: 9
  }
];
