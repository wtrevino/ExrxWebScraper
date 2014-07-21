from scrapy.spider import Spider
from scrapy.selector import Selector
from exrxProject.items import ExrxItem, ExrxCategory, ExrxExercise
from scrapy.http import Request
import re

#TO OUTPUT TO JSON RUN THIS COMMAND
#run in dir: exrxScraper/exrxProject
#scrapy crawl exrx -o items.json -t json

NON_DIR_URLS = [
    'http://www.exrx.net/Lists/OlympicWeightlifting.html',
    'http://www.exrx.net/Lists/PowerExercises.html',
    'http://www.exrx.net/Lists/KettlebellExercises.html',
    'http://www.exrx.net/Lists/CardioExercises.html',
]


class exrxScraperSpider(Spider):
    name = "exrx"
    allowed_domains = ["exrx.net"]
    start_urls = [
            "http://www.exrx.net/Lists/Directory.html",
            ] + NON_DIR_URLS

    def parseExercise(self, response):
        sel = Selector(response)
        exerciseItems = []

        #instructionsTree = sel.xpath('//h2[contains(text(), "Instructions")]')
        #print instructionsTree
        item = ExrxExercise()
        #prep = instructionsTree.xpath('./../dl/dd[contains(text(), "Preparation")]')
        #item['preparation'] = prep.xpath('./text()').extract()
        #execution = instructionsTree.xpath('./../dl/dd[contains(text(), "Execution")]')
        #item['execution'] = execution.xpath('./text()').extract()
        #exerciseItems.append(item)

        item['link'] = response.url

        category = response.url.split('/')[3]
        sub_category = response.url.split('/')[4]
        item['category'] = category
        item['sub_category'] = sub_category

        title = response.xpath('//h1/a/text()').extract()[0]

        # Remove whitespace from title
        title = title.replace('\n', ' ').replace('\r', ' ')
        title = " ".join(title.split())
        item['title'] = title

        instructions = response.xpath('//table[contains(@border, "1")]/tr/td')[0].xpath('.//text()').extract()
        instructions = ''.join(instructions)
        item['instructions'] = instructions

        images = response.xpath('//img/@src').extract()
        if len(images) > 1:
            image = images[1]
            image = image.replace('../../', 'http://www.exrx.net/')
            item['image'] = image
        else:
            item['image'] = "No image available."

        muscles = response.xpath('//table[contains(@border, "1")]/tr/td')[1].xpath('.//*[not(self::blockquote)]/text()').extract()
        muscles = ''.join(muscles)
        if 'MusclesTarget' in muscles:
            muscles = 'Target \n' + muscles.split('MusclesTarget')[1]
            muscles = muscles.replace('Synergists', 'Synergists\n')
            muscles = muscles.replace('Stabilizers', 'Stabilizers\n')

        if 'Force (Articulation)' in muscles:
            muscles = 'Force (Articulation) \n' + muscles.split('Force (Articulation)')[1]


        item['muscles'] = muscles

        print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
        print 'Title: %s' % title
        print 'Category: %s, Sub Category: %s' % (category, sub_category)
        print

        print 'Instructions:'
        print instructions
        print

        print 'Muscles:'
        print muscles
        print

        print 'Image:'
        print image
        print

        yield item



    def getEquipmentName(self, sel):
        count = 0
        parentName = sel.xpath('../text()').extract()
        return sel.xpath('.//ancestor::*[contains(text(), "Barbell")]').extract()

    def parseCategory(self, response):
        sel = Selector(response)
        sites = sel.xpath('//ul/li/a')
        for sel in sites:
            validLinks = sel.xpath('./@href[contains(., "WeightExercises") \
                            or contains(., "Plyometrics") \
                            or contains(., "Stretches")]')
            links = validLinks.extract()
            link = ''
            title = ''


            titleList = validLinks.xpath('./text()').extract()
            if titleList == []:
                titleList = sel.xpath('./i/text()').extract()
            newTitleList = [re.sub(r'\r\n\s*', ' ', title).replace('\n', ' ').replace('\r', ' ') for title in titleList]
            for s in newTitleList:
                title = s
            for s in links:
                link = 'http://www.exrx.net/' + s.replace('../../','' )

            if (not (link == '')) and (not (title == '')):
                #item = ExrxCategory()
                #item['link'] = link
                #item['title'] = title
                #yield item
                req = Request(link, callback=self.parseExercise)
                yield req


    def parse(self, response):

        if response.url in NON_DIR_URLS:
            for link in response.xpath('//ul/li/a/@href'):
                href = link.extract()
                if '..' in href:
                    href = href.replace('../', 'http://www.exrx.net/')
                    req = Request(href, callback=self.parseExercise)
                    yield req

        sel = Selector(response)
        exercises = sel.xpath('//h2[contains(text(), "Exercises")]')
        sites = exercises.xpath('./..//ul//li')
        items = []
        for sel in sites:
            link = sel.xpath('./a/@href').extract()
            for s in link:
                req = Request('http://www.exrx.net/Lists/' + s, callback=self.parseCategory)
                yield req

