# address_bleach
Python 3.6+ Home Project: Standardizing Address data and making it easier to compare them.

Use at your own risk/discretion.  This project is merely a means to simplify my constant struggle with address data.
Sure, there are probably really nice, expensive products out there.  That's great, but it's not always immediately
available or useful in all cases.  So, out of my own blood, tears, and frustration, I built this project.

First and foremost, it ain't perfect and I'm certain that there are a million other ways I could have written or performed
the processes (see: really nice, expensive products out there).  This is simple, dirty, and, depending on who you ask,
effective for the purpose it serves.

With that out of the way, most of my identification decisions and data were based upon reading portions of the 137 page
Street Address Data Standard document provided by the Federal Geographic Data Committee, dated November 2005.  There may
be a more current document, but this was the most relevant I could find in my research.

So...what does it do?  It's a Ptyhon module that allows you to pass in an Address and perform a breakdown of its details.
Essentially, 123 Main Street gets broken down into:

Street Number: 123
Street Name: Main
Street Suffix: Street

And other various details.  These become new variables that you can call. Helpful depending on what you need to do with
the data.

There's currently one function compare(address1, address2).  It does just that.  It attempts to determine if the two addresses
are indeed a match based upon the details of each address.

TL/DR: This is my first Python Project that wasn't specific to a situation, targeted to a problem and I wanted
to solve it without the need of purchasing expensive software.  It sucks in addresses, breaks them down for you, and gives
you the ability to compare them.
