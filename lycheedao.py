# -*- coding: utf-8 -*-

import MySQLdb
import datetime
import traceback


class LycheeDAO:
    """
    Implements linking with Lychee DB
    """

    db = None
    conf = None
    albumslist = {}

    def __init__(self, conf):
        """
        Takes a dictionnary of conf as input
        """

        self.conf = conf
        self.db = MySQLdb.connect(host=self.conf["dbHost"],
                                  user=self.conf["dbUser"],
                                  passwd=self.conf["dbPassword"],
                                  db=self.conf["db"])

        if self.conf["dropdb"]:
            self.dropAll()

        self.loadAlbumList()

    def loadAlbumList(self):
        """
        retrieve all albums in a dictionnary key=title value=id
        and put them in self.albumslist
        returns self.albumlist
        """
        #Load album list
        cur = self.db.cursor()
        cur.execute("SELECT title,id from lychee_albums")
        rows = cur.fetchall()
        for row in rows:
            self.albumslist[row[0]] = row[1]

        if self.conf['verbose']:
            print "INFO album list in db:", self.albumslist
        return self.albumslist

    def albumExists(self, albumname):
        """
        Check if an album exists based on its name
        Returns None or the albumid if it exists
        """

        if albumname in self.albumslist.keys():
            return self.albumslist[albumname]
        else:
            return None

    def photoExists(self, photo):
        """
        Check if an album exists based on its original name
        Parameter:
        - photo: a valid LycheePhoto object
        Returns a boolean
        """
        res = False
        try:
            query = ("select * from lychee_photos where album=" + str(photo.albumid) +
                     " and import_name = '" + photo.originalname + "'")
            cur = self.db.cursor()
            cur.execute(query)
            row = cur.fetchall()
            if len(row) != 0:
                res = True

        except Exception:
            print "ERROR photoExists:", photo.srcfullpath, "won't be added to lychee"
            traceback.print_exc()
            res = True
        finally:
            return res

    def createAlbum(self, name):
        """
        Creates an album
        Parameter:
        - name: the album name
        Returns the created albumid or None
        """
        id = None
        query = ("insert into lychee_albums (title, sysdate, public, password) values ('" +
                 name + "','" + datetime.date.today().isoformat() + "'," +
                 str(self.conf["publicAlbum"]) + ", NULL)")
        try:
            cur = self.db.cursor()
            cur.execute(query)
            self.db.commit()

            #cur.execute(query, (name, self.conf["publicAlbum"]))
            query = "select id from lychee_albums where title='" + name + "'"
            cur.execute(query)
            row = cur.fetchone()
            self.albumslist[name] = row[0]
            id = row[0]
            if self.conf["verbose"]:
                print "INFO album created:", name

        except Exception:
            print "createAlbum", Exception
            traceback.print_exc()
            id = None
        finally:
            return id

    def eraseAlbum(self, albumid):
        """
        Deletes all photos of an album but don't delete the album itself
        Parameters:
        - albumid: the album to erase id
        Return list of the erased photo url
        """
        res = []
        query = "delete from lychee_photos where album = " + str(albumid) + ''
        selquery = "select url from lychee_photos where album = " + str(albumid) + ''
        try:
            cur = self.db.cursor()
            cur.execute(selquery)
            rows = cur.fetchall()
            for row in rows:
                res.append(row[0])
            cur.execute(query)
            self.db.commit()
        except Exception:
            print "eraseAlbum", Exception
            traceback.print_exc()
        finally:
            return res

    def listAllPhoto(self):
        """
        Lists all photos in leeche db (used to delete all files)
        Return a photo url list
        """
        res = []
        selquery = "select url from lychee_photos"
        try:
            cur = self.db.cursor()
            cur.execute(selquery)
            rows = cur.fetchall()
            for row in rows:
                res.append(row[0])
        except Exception:
            print "listAllPhoto", Exception
            traceback.print_exc()
        finally:
            return res

    def addFileToAlbum(self, photo):
        """
        Add a photo to an album
        Parameter:
        - photo: a valid LycheePhoto object
        Returns a boolean
        """
        res = True
        #print photo
        query = ("insert into lychee_photos " +
                 "(id, url, public, type, width, height, " +
                 "size,  sysdate, systime, star, " +
                 "thumbUrl, album,iso, aperture, make, " +
                 "model, shutter, focal, takedate, " +
                 "taketime, import_name, description, title) " +
                 "values " +
                 "({}, '{}', {}, '{}' ,{}, {}, " +
                 "'{}','{}', '{}', {}, " +
                 "'{}',{}, '{}','{}','{}', " +
                 "'{}', '{}', '{}', '{}', " +
                 "'{}', '{}', '{}', '{}')"
                 ).format(photo.id, photo.url, self.conf["publicAlbum"], photo.type, photo.width, photo.height,
                          photo.size, photo.sysdate, photo.systime, self.conf["starPhoto"],
                          photo.thumbUrl, photo.albumid, photo.exif.iso, photo.exif.aperture, photo.exif.make,
                          photo.exif.model, photo.exif.shutter, photo.exif.focal, photo.exif.takedate,
                          photo.exif.taketime, photo.originalname, '', '')
        #print query

        try:
            cur = self.db.cursor()
            res = cur.execute(query)
            self.db.commit()
        except Exception:
            print "addFileToAlbum", Exception
            traceback.print_exc()
            res = False
        finally:
            return res

    def close(self):
        """
        Close DB Connection
        Returns nothing
        """
        if self.db:
            self.db.close()

    def dropAll(self):
        """
        Drop all albums and photos from DB
        Returns nothing
        """
        try:
            cur = self.db.cursor()
            cur.execute("delete from lychee_albums")
            cur.execute("delete from lychee_photos")
            self.db.commit()
        except Exception:
            print "dropAll", Exception
            traceback.print_exc()
