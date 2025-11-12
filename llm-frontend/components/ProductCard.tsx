"use client";

import React from 'react';
import Image from 'next/image';

interface ProductCardProps {
  title: string;
  description?: string;
  price?: string;
  rating?: number;
  reviews_count?: number;
  image?: string;
  url: string;
  seller?: string;
  tag?: string;
  delivery?: string;
}

export default function ProductCard({
  title,
  description,
  price,
  rating,
  reviews_count,
  image,
  url,
  seller,
  tag,
  delivery
}: ProductCardProps) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden group flex-shrink-0 w-64"
      data-hover-id={url || title}
    >
      <div className="flex gap-3 p-3">
        {/* Product Image */}
        {image && (
          <div className="flex-shrink-0 w-24 h-24 bg-gray-100 rounded-md overflow-hidden relative">
            <img
              src={image}
              alt={title}
              className="w-full h-full object-contain"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors">
            {title}
          </h3>

          {/* Price */}
          {price && (
            <div className="mt-1">
              <span className="text-lg font-semibold text-gray-900">{price}</span>
            </div>
          )}

          {/* Rating & Reviews */}
          {rating && (
            <div className="flex items-center gap-2 mt-1">
              <div className="flex items-center">
                <span className="text-yellow-400 text-sm">★</span>
                <span className="text-sm text-gray-700 ml-1">{rating}</span>
              </div>
              {reviews_count && (
                <span className="text-xs text-gray-500">
                  ({reviews_count.toLocaleString()})
                </span>
              )}
            </div>
          )}

          {/* Seller */}
          {seller && (
            <div className="mt-1 text-xs text-gray-500">
              from <span className="font-medium">{seller}</span>
            </div>
          )}

          {/* Tags & Delivery */}
          <div className="flex flex-wrap gap-2 mt-2">
            {tag && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                {tag}
              </span>
            )}
            {delivery && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                {delivery}
              </span>
            )}
          </div>
        </div>
      </div>
    </a>
  );
}
