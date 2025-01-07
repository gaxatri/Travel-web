'use client';
// components/RecommendedLocations.js

import { useEffect, useState } from 'react';
import Papa from 'papaparse';
import styles from './allLocation.module.css';
import Button from './buttons/button.js'; // Import Button component
import Link from 'next/link';

const RecommendedLocations = () => {
  const [locations, setLocations] = useState([]);
  const [userData, setUserData] = useState({
    addedLocations: [],
    likedLocations: [],
    visitedLocations: [],
  });
  const [userRecommendations, setUserRecommendations] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch user data
  useEffect(() => {
    fetch('/userData/userData.json')
      .then((response) => {
        if (!response.ok) throw new Error('Failed to fetch user data.');
        return response.json();
      })
      .then((userData) => {
        const recommendations = userData['00']?.recommended || [];
        setUserRecommendations(recommendations);
        setUserData({
          addedLocations: userData['00']?.addedLocations || [],
          likedLocations: userData['00']?.likedLocations || [],
          visitedLocations: userData['00']?.visitedLocations || [],
        });
      })
      .catch((err) => {
        setError(`User data error: ${err.message}`);
      });
  }, []);

  useEffect(() => {
    if (userRecommendations.length === 0) {
      setIsLoading(false);
      return;
    }

    // Fetch and parse the CSV file for location data
    fetch('/locationData/dataset.csv')
      .then((response) => {
        if (!response.ok) throw new Error('Failed to fetch location data.');
        return response.text();
      })
      .then((csvText) => {
        Papa.parse(csvText, {
          complete: (result) => {
            const filteredLocations = result.data.filter((location) =>
              userRecommendations.includes(location.Name) // Compare by Name
            );
            setLocations(filteredLocations);
            setIsLoading(false);
          },
          header: true, // Treats the first row as headers
        });
      })
      .catch((err) => {
        setError(`Location data error: ${err.message}`);
        setIsLoading(false);
      });
  }, [userRecommendations]);

  const handleAction = (locationName, action) => {
    fetch('/api/updateUserData', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId: '00', // Use the actual user ID
        location: locationName,
        action: action,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log('User data updated:', data);
        // Update user data in state after action
        setUserData((prevData) => {
          const updatedData = { ...prevData };

          if (action === 'add') {
            updatedData.addedLocations.push(locationName);
          } else if (action === 'remove') {
            updatedData.addedLocations = updatedData.addedLocations.filter(
              (loc) => loc !== locationName
            );
          } else if (action === 'like') {
            updatedData.likedLocations.push(locationName);
          } else if (action === 'removeLike') {
            updatedData.likedLocations = updatedData.likedLocations.filter(
              (loc) => loc !== locationName
            );
          } else if (action === 'visit') {
            updatedData.visitedLocations.push(locationName);
          } else if (action === 'removeVisit') {
            updatedData.visitedLocations = updatedData.visitedLocations.filter(
              (loc) => loc !== locationName
            );
          }
          return updatedData;
        });
      })
      .catch((error) => {
        console.error('Error updating user data:', error);
      });
  };

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p className={styles.errorMessage}>{error}</p>;

  return (
    <div className={styles.locationGrid}>
      {locations.length === 0 ? (
        <p>No locations to recommend.</p>
      ) : (
        <div className={styles.gridContainer}>
          {locations.map((location, index) => (
            <div key={index} className={styles.locationCard}>
              <img src={location.url} alt={location.Name} />
              <h3>{location.Name}</h3>
              <p>{location.Category}</p>
              <p>{location.Location}</p>
              <div className={styles.buttons}>
                <Button
                  label="Add"
                  onClick={() =>
                    userData.addedLocations.includes(location.Name)
                      ? handleAction(location.Name, 'remove')
                      : handleAction(location.Name, 'add')
                  }
                  disabled={false}
                  isAdded={userData.addedLocations.includes(location.Name)}
                />
                <Button
                  label="Like"
                  onClick={() =>
                    userData.likedLocations.includes(location.Name)
                      ? handleAction(location.Name, 'removeLike')
                      : handleAction(location.Name, 'like')
                  }
                  disabled={false}
                  isLiked={userData.likedLocations.includes(location.Name)}
                />
                <Button
                  label="Already Visited"
                  onClick={() =>
                    userData.visitedLocations.includes(location.Name)
                      ? handleAction(location.Name, 'removeVisit')
                      : handleAction(location.Name, 'visit')
                  }
                  disabled={false}
                  isVisited={userData.visitedLocations.includes(location.Name)}
                />
              </div>
              <Link href={`/locations/${encodeURIComponent(location.Name)}`}>
                <div className={styles.locationLink}>View Details</div>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecommendedLocations;